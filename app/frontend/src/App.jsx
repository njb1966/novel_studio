import { useState, useEffect, useCallback } from 'react';
import { checkHealth, getProjects, createProject, importProject } from './api';
import ProjectWorkspace from './ProjectWorkspace';
import './App.css';

const EMPTY_CREATE = {
  title: '',
  genre: '',
  pov: '',
  tense: '',
  target_word_count: 80000,
};

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return iso;
  }
}

function Modal({ title, onClose, children }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{title}</h2>
          <button className="modal-close" onClick={onClose} aria-label="Close">
            &times;
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

function NewProjectModal({ onClose, onCreated }) {
  const [form, setForm] = useState(EMPTY_CREATE);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const set = field => e => setForm(f => ({ ...f, [field]: e.target.value }));

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.title.trim()) { setError('Title is required.'); return; }
    setSaving(true);
    setError('');
    try {
      const project = await createProject({
        ...form,
        target_word_count: parseInt(form.target_word_count, 10) || 80000,
      });
      onCreated(project);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title="New Project" onClose={onClose}>
      <form onSubmit={handleSubmit} className="modal-form">
        <label>
          Title <span className="required">*</span>
          <input
            type="text"
            value={form.title}
            onChange={set('title')}
            placeholder="My Novel"
            autoFocus
          />
        </label>
        <label>
          Genre
          <input
            type="text"
            value={form.genre}
            onChange={set('genre')}
            placeholder="e.g. literary fiction"
          />
        </label>
        <label>
          Point of View
          <input
            type="text"
            value={form.pov}
            onChange={set('pov')}
            placeholder="e.g. third limited"
          />
        </label>
        <label>
          Tense
          <input
            type="text"
            value={form.tense}
            onChange={set('tense')}
            placeholder="e.g. past"
          />
        </label>
        <label>
          Target Word Count
          <input
            type="number"
            value={form.target_word_count}
            onChange={set('target_word_count')}
            min={1000}
            step={1000}
          />
        </label>
        {error && <p className="form-error">{error}</p>}
        <div className="modal-actions">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Creating...' : 'Create Project'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function ImportProjectModal({ onClose, onImported }) {
  const [folderPath, setFolderPath] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!folderPath.trim()) { setError('Folder path is required.'); return; }
    setSaving(true);
    setError('');
    try {
      const project = await importProject(folderPath.trim());
      onImported(project);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title="Import Project" onClose={onClose}>
      <form onSubmit={handleSubmit} className="modal-form">
        <p className="modal-hint">
          Point to a folder containing markdown files (NOVEL_SPEC.md, etc.).
          The title will be read from the file or inferred from the folder name.
        </p>
        <label>
          Folder Path <span className="required">*</span>
          <input
            type="text"
            value={folderPath}
            onChange={e => setFolderPath(e.target.value)}
            placeholder="/path/to/my-novel-folder"
            autoFocus
          />
        </label>
        {error && <p className="form-error">{error}</p>}
        <div className="modal-actions">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Importing...' : 'Import Project'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function ProjectCard({ project, onOpen }) {
  return (
    <div className="project-card">
      <div className="project-card-body">
        <h3 className="project-title">{project.title}</h3>
        <div className="project-meta">
          {project.genre && <span className="tag">{project.genre}</span>}
          {project.pov && <span className="tag">{project.pov}</span>}
          {project.tense && <span className="tag">{project.tense}</span>}
        </div>
        <div className="project-details">
          <span className={`status-badge status-${project.status}`}>{project.status}</span>
          <span className="project-date">Created {formatDate(project.created_at)}</span>
          {project.target_word_count > 0 && (
            <span className="word-count">
              Target: {project.target_word_count.toLocaleString()} words
            </span>
          )}
          {project.actual_word_count > 0 && (
            <span className="word-count word-count-actual">
              Written: {project.actual_word_count.toLocaleString()} words (approved)
            </span>
          )}
        </div>
      </div>
      <div className="project-card-actions">
        <button className="btn-open" onClick={() => onOpen(project)}>
          Open
        </button>
      </div>
    </div>
  );
}

export default function App() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [backendOnline, setBackendOnline] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);

  const loadProjects = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getProjects();
      setProjects(data);
      setBackendOnline(true);
    } catch {
      setBackendOnline(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProjects();
    const interval = setInterval(async () => {
      const ok = await checkHealth();
      setBackendOnline(ok);
    }, 5000);
    return () => clearInterval(interval);
  }, [loadProjects]);

  function handleCreated(project) {
    setProjects(prev => [project, ...prev]);
    setShowNew(false);
  }

  function handleImported(project) {
    setProjects(prev => [project, ...prev]);
    setShowImport(false);
  }

  if (selectedProject) {
    return (
      <ProjectWorkspace
        project={selectedProject}
        onBack={() => setSelectedProject(null)}
      />
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-inner">
          <h1 className="app-title">Novel Studio</h1>
          <div className="header-actions">
            <button
              className="btn-primary"
              onClick={() => setShowNew(true)}
              disabled={!backendOnline}
            >
              + New Project
            </button>
            <button
              className="btn-secondary"
              onClick={() => setShowImport(true)}
              disabled={!backendOnline}
            >
              Import
            </button>
          </div>
        </div>
      </header>

      <main className="main-content">
        {loading ? (
          <div className="state-message">Loading projects...</div>
        ) : !backendOnline ? (
          <div className="state-message offline">
            <p>Could not connect to the backend.</p>
            <p className="state-hint">
              Start it with: <code>cd app/backend &amp;&amp; bash start.sh</code>
            </p>
          </div>
        ) : projects.length === 0 ? (
          <div className="state-message empty">
            <p>No projects yet.</p>
            <p className="state-hint">Create a new project or import an existing folder.</p>
          </div>
        ) : (
          <div className="project-list">
            {projects.map(p => (
              <ProjectCard key={p.id} project={p} onOpen={setSelectedProject} />
            ))}
          </div>
        )}
      </main>

      <footer className="status-bar">
        <span className={`backend-status ${backendOnline ? 'online' : 'offline'}`}>
          Backend: {backendOnline ? 'Connected' : 'Offline'}
        </span>
        {backendOnline && (
          <span className="project-count">
            {projects.length} project{projects.length !== 1 ? 's' : ''}
          </span>
        )}
      </footer>

      {showNew && (
        <NewProjectModal onClose={() => setShowNew(false)} onCreated={handleCreated} />
      )}
      {showImport && (
        <ImportProjectModal onClose={() => setShowImport(false)} onImported={handleImported} />
      )}
    </div>
  );
}
