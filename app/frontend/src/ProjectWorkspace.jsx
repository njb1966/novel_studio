import { useState, useEffect, useCallback } from 'react';
import { getFile, saveFile, syncProject, getChapters, getScaffoldStatus, scaffoldProject } from './api';
import ChapterPipeline from './ChapterPipeline';
import ContinuityExplorer from './ContinuityExplorer';
import ExportPanel from './ExportPanel';
import QAReportsPanel from './QAReportsPanel';
import './ProjectWorkspace.css';

const EDITOR_ITEMS = [
  { label: 'Novel Spec',  file: 'novel_spec.md' },
  { label: 'Outline',     file: 'outline.md' },
  { label: 'Characters',  file: 'character_bible.md' },
  { label: 'World Bible', file: 'world_bible.md' },
];

const PANEL_ITEMS = [
  { label: 'Chapters',    panel: 'chapters' },
  { label: 'Continuity',  panel: 'continuity' },
  { label: 'QA Reports',  panel: 'qa' },
  { label: 'Export',      panel: 'export' },
];

const STUB_ITEMS = [];

function wordCount(text) {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

// ── Status badge ────────────────────────────────────────────────────────────
function StatusBadge({ status }) {
  const cls =
    status === 'final'    ? 'badge badge-final'    :
    status === 'approved' ? 'badge badge-approved' :
                            'badge badge-draft';
  return <span className={cls}>{status}</span>;
}

// ── Chapter list ────────────────────────────────────────────────────────────
function ChapterList({ projectId, refreshKey, onSelectChapter }) {
  const [chapters, setChapters] = useState(null);
  const [error, setError]       = useState('');

  useEffect(() => {
    let cancelled = false;
    getChapters(projectId)
      .then(data => { if (!cancelled) setChapters(data); })
      .catch(err  => { if (!cancelled) setError(err.message); });
    return () => { cancelled = true; };
  }, [projectId, refreshKey]);

  if (error) {
    return <div className="chapter-list-empty">Error loading chapters: {error}</div>;
  }

  if (chapters === null) {
    return <div className="chapter-list-empty">Loading chapters...</div>;
  }

  if (chapters.length === 0) {
    return (
      <div className="chapter-list-empty">
        No chapters synced yet.<br />
        Click <strong>Sync</strong> in the toolbar to parse your outline.
      </div>
    );
  }

  return (
    <div className="chapter-list">
      {chapters.map(ch => (
        <div
          key={ch.id}
          className="chapter-row chapter-row-clickable"
          onClick={() => onSelectChapter(ch)}
          title="Open chapter pipeline"
        >
          <div className="chapter-row-header">
            <span className="chapter-number">Ch {ch.chapter_number}</span>
            <span className="chapter-title">{ch.title || '(untitled)'}</span>
            <span className="chapter-pov">
              {ch.pov_character ? `POV: ${ch.pov_character}` : ''}
            </span>
            <StatusBadge status={ch.status} />
          </div>
          {ch.outline_goal && (
            <div className="chapter-goal">
              Goal: {ch.outline_goal}
            </div>
          )}
          {ch.summary_snippet && (
            <div className="chapter-summary-snippet">
              {ch.summary_snippet}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Scaffold modal ───────────────────────────────────────────────────────────
function ScaffoldModal({ project, onClose, onDone }) {
  const [status, setStatus]   = useState(null);   // scaffold/status result
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [force, setForce]     = useState(false);
  const [result, setResult]   = useState(null);
  const [error, setError]     = useState('');

  useEffect(() => {
    getScaffoldStatus(project.id)
      .then(s  => { setStatus(s); setLoading(false); })
      .catch(() => { setLoading(false); });
  }, [project.id]);

  async function handleRun() {
    setRunning(true);
    setError('');
    try {
      const res = await scaffoldProject(project.id, force);
      setResult(res);
      if (res.generated.length > 0) onDone();
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  }

  const FILE_LABELS = {
    'novel_spec.md':      'Novel Spec',
    'character_bible.md': 'Character Bible',
    'world_bible.md':     'World Bible',
    'continuity_log.md':  'Continuity Log',
  };

  const existingFiles = status
    ? Object.entries(status.files).filter(([, has]) => has).map(([f]) => f)
    : [];
  const missingFiles = status
    ? Object.entries(status.files).filter(([, has]) => !has).map(([f]) => f)
    : [];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal scaffold-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Scaffold Documents</h2>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>

        {loading ? (
          <p className="scaffold-hint">Checking project files...</p>
        ) : !status?.has_outline ? (
          <div className="scaffold-body">
            <p className="scaffold-hint scaffold-warn">
              OUTLINE.md is empty or missing. Write your outline first, then scaffold.
            </p>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={onClose}>Close</button>
            </div>
          </div>
        ) : result ? (
          <div className="scaffold-body">
            {result.generated.length > 0 && (
              <div className="scaffold-section">
                <p className="scaffold-section-label">Generated</p>
                <ul className="scaffold-file-list">
                  {result.generated.map(f => (
                    <li key={f} className="scaffold-file-item scaffold-file-ok">
                      {FILE_LABELS[f] || f}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {result.skipped.length > 0 && (
              <div className="scaffold-section">
                <p className="scaffold-section-label">Skipped (already exist)</p>
                <ul className="scaffold-file-list">
                  {result.skipped.map(f => (
                    <li key={f} className="scaffold-file-item scaffold-file-skip">
                      {FILE_LABELS[f] || f}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {result.errors.length > 0 && (
              <div className="scaffold-section">
                <p className="scaffold-section-label scaffold-warn">Errors</p>
                <ul className="scaffold-file-list">
                  {result.errors.map(e => (
                    <li key={e.file} className="scaffold-file-item scaffold-file-err">
                      {FILE_LABELS[e.file] || e.file}: {e.error}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div className="modal-actions">
              <button className="btn-primary" onClick={onClose}>Done</button>
            </div>
          </div>
        ) : (
          <div className="scaffold-body">
            <p className="scaffold-hint">
              Generate foundational documents from your outline using AI.
              This makes {missingFiles.length > 0 ? missingFiles.length : 'all'} LLM
              call{missingFiles.length !== 1 ? 's' : ''} in parallel — expect 30–90 seconds.
            </p>

            {existingFiles.length > 0 && (
              <div className="scaffold-section">
                <p className="scaffold-section-label">Already have content</p>
                <ul className="scaffold-file-list">
                  {existingFiles.map(f => (
                    <li key={f} className="scaffold-file-item scaffold-file-skip">
                      {FILE_LABELS[f] || f}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {missingFiles.length > 0 && (
              <div className="scaffold-section">
                <p className="scaffold-section-label">Will generate</p>
                <ul className="scaffold-file-list">
                  {missingFiles.map(f => (
                    <li key={f} className="scaffold-file-item scaffold-file-ok">
                      {FILE_LABELS[f] || f}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {existingFiles.length > 0 && (
              <label className="scaffold-force-row">
                <input
                  type="checkbox"
                  checked={force}
                  onChange={e => setForce(e.target.checked)}
                />
                Overwrite existing files
              </label>
            )}

            {error && <p className="form-error">{error}</p>}

            <div className="modal-actions">
              <button className="btn-secondary" onClick={onClose} disabled={running}>
                Cancel
              </button>
              <button
                className="btn-primary"
                onClick={handleRun}
                disabled={running || (!force && missingFiles.length === 0)}
              >
                {running ? 'Generating…' : 'Generate'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Workspace ────────────────────────────────────────────────────────────────
export default function ProjectWorkspace({ project, onBack }) {
  // 'editor:filename' or 'panel:chapters'
  const [activeView, setActiveView] = useState('editor:novel_spec.md');

  const [content, setContent]           = useState('');
  const [savedContent, setSavedContent] = useState('');
  const [loading, setLoading]           = useState(false);
  const [saving, setSaving]             = useState(false);
  const [error, setError]               = useState('');

  const [syncing, setSyncing]         = useState(false);
  const [syncStatus, setSyncStatus]   = useState('');
  const [chaptersKey, setChaptersKey] = useState(0);
  const [showScaffold, setShowScaffold] = useState(false);

  // Chapter pipeline — null means showing the list
  const [selectedChapter, setSelectedChapter] = useState(null);

  const isEditorView = activeView.startsWith('editor:');
  const activeFile   = isEditorView ? activeView.slice(7) : null;
  const activePanel  = !isEditorView ? activeView.slice(6) : null;

  const isDirty = isEditorView && content !== savedContent;

  // ── Load file ──────────────────────────────────────────────────────────
  const loadFile = useCallback(async (filename) => {
    setLoading(true);
    setError('');
    try {
      const data = await getFile(project.id, filename);
      setContent(data.content);
      setSavedContent(data.content);
    } catch (err) {
      setError(`Could not load ${filename}: ${err.message}`);
      setContent('');
      setSavedContent('');
    } finally {
      setLoading(false);
    }
  }, [project.id]);

  useEffect(() => {
    if (isEditorView && activeFile) {
      loadFile(activeFile);
    }
  }, [loadFile, activeView, isEditorView, activeFile]);

  // ── Sidebar navigation ─────────────────────────────────────────────────
  function switchView(next) {
    if (next === activeView) return;
    if (isDirty) {
      const ok = window.confirm('You have unsaved changes. Switch and discard them?');
      if (!ok) return;
    }
    setError('');
    setActiveView(next);
  }

  // ── Save ───────────────────────────────────────────────────────────────
  async function handleSave() {
    if (!isDirty || saving) return;
    setSaving(true);
    setError('');
    try {
      await saveFile(project.id, activeFile, content);
      setSavedContent(content);
    } catch (err) {
      setError(`Save failed: ${err.message}`);
    } finally {
      setSaving(false);
    }
  }

  // ── Sync ───────────────────────────────────────────────────────────────
  async function handleSync() {
    if (syncing) return;
    setSyncing(true);
    setSyncStatus('Syncing...');
    try {
      const result = await syncProject(project.id);
      setSyncStatus(
        `Synced: ${result.chapters_synced} chapters, ${result.characters_synced} characters`
      );
      setChaptersKey(k => k + 1);
      setTimeout(() => setSyncStatus(''), 4000);
    } catch (err) {
      setSyncStatus(`Sync failed: ${err.message}`);
      setTimeout(() => setSyncStatus(''), 5000);
    } finally {
      setSyncing(false);
    }
  }

  // ── Back ───────────────────────────────────────────────────────────────
  function handleBack() {
    if (isDirty) {
      const ok = window.confirm('You have unsaved changes. Go back anyway?');
      if (!ok) return;
    }
    onBack();
  }

  const activeSidebarLabel =
    EDITOR_ITEMS.find(i => i.file === activeFile)?.label ??
    PANEL_ITEMS.find(i => i.panel === activePanel)?.label ??
    activeFile;

  // ── Chapter pipeline overlay ───────────────────────────────────────────
  if (selectedChapter) {
    return (
      <div className="workspace">
        <header className="ws-header">
          <button className="ws-back btn-secondary" onClick={handleBack}>
            &#8592; Back
          </button>
          <h1 className="ws-title">{project.title}</h1>
        </header>
        <div className="ws-body" style={{ overflow: 'hidden' }}>
          <nav className="ws-sidebar">
            <div className="sidebar-section-label">Documents</div>
            {EDITOR_ITEMS.map(item => (
              <button
                key={item.file}
                className="sidebar-item"
                onClick={() => { setSelectedChapter(null); switchView('editor:' + item.file); }}
              >
                {item.label}
              </button>
            ))}
            <div className="sidebar-divider" />
            <div className="sidebar-section-label">Project</div>
            <button
              className="sidebar-item active"
              onClick={() => setSelectedChapter(null)}
            >
              Chapters
            </button>
            <button
              className="sidebar-item"
              onClick={() => { setSelectedChapter(null); switchView('panel:continuity'); }}
            >
              Continuity
            </button>
            <button
              className="sidebar-item"
              onClick={() => { setSelectedChapter(null); switchView('panel:qa'); }}
            >
              QA Reports
            </button>
            <button
              className="sidebar-item"
              onClick={() => { setSelectedChapter(null); switchView('panel:export'); }}
            >
              Export
            </button>
            {STUB_ITEMS.length > 0 && (
              <>
                <div className="sidebar-divider" />
                <div className="sidebar-section-label">Coming Soon</div>
                {STUB_ITEMS.map(item => (
                  <button
                    key={item.label}
                    className="sidebar-item sidebar-stub"
                    disabled
                    title={`Coming in Milestone ${item.milestone}`}
                  >
                    {item.label}
                  </button>
                ))}
              </>
            )}
          </nav>
          <main className="ws-editor-panel">
            <ChapterPipeline
              project={project}
              chapter={selectedChapter}
              onBack={() => setSelectedChapter(null)}
              onOpenContinuity={() => {
                setSelectedChapter(null);
                switchView('panel:continuity');
              }}
            />
          </main>
        </div>
      </div>
    );
  }

  return (
    <div className="workspace">

      {/* Top bar */}
      <header className="ws-header">
        <button className="ws-back btn-secondary" onClick={handleBack}>
          &#8592; Back
        </button>
        <h1 className="ws-title">{project.title}</h1>

        {syncStatus && (
          <span className="ws-sync-status">{syncStatus}</span>
        )}

        <button
          className="btn-secondary ws-sync"
          onClick={handleSync}
          disabled={syncing}
        >
          {syncing ? 'Syncing...' : 'Sync'}
        </button>

        <button
          className="btn-secondary ws-scaffold"
          onClick={() => setShowScaffold(true)}
          title="Generate NOVEL_SPEC, CHARACTER_BIBLE, WORLD_BIBLE, CONTINUITY_LOG from outline"
        >
          Scaffold Docs
        </button>

        <button
          className="btn-primary ws-save"
          onClick={handleSave}
          disabled={!isDirty || saving}
        >
          {saving ? 'Saving...' : 'Save'}
        </button>
      </header>

      {showScaffold && (
        <ScaffoldModal
          project={project}
          onClose={() => setShowScaffold(false)}
          onDone={() => {
            setShowScaffold(false);
            if (isEditorView && activeFile) loadFile(activeFile);
          }}
        />
      )}

      <div className="ws-body">

        {/* Sidebar */}
        <nav className="ws-sidebar">
          <div className="sidebar-section-label">Documents</div>
          {EDITOR_ITEMS.map(item => (
            <button
              key={item.file}
              className={`sidebar-item${activeView === 'editor:' + item.file ? ' active' : ''}`}
              onClick={() => switchView('editor:' + item.file)}
            >
              {item.label}
            </button>
          ))}

          <div className="sidebar-divider" />

          <div className="sidebar-section-label">Project</div>
          {PANEL_ITEMS.map(item => (
            <button
              key={item.panel}
              className={`sidebar-item${activeView === 'panel:' + item.panel ? ' active' : ''}`}
              onClick={() => switchView('panel:' + item.panel)}
            >
              {item.label}
            </button>
          ))}

          {STUB_ITEMS.length > 0 && (
            <>
              <div className="sidebar-divider" />
              <div className="sidebar-section-label">Coming Soon</div>
              {STUB_ITEMS.map(item => (
                <button
                  key={item.label}
                  className="sidebar-item sidebar-stub"
                  disabled
                  title={`Coming in Milestone ${item.milestone}`}
                >
                  {item.label}
                </button>
              ))}
            </>
          )}
        </nav>

        {/* Main panel */}
        <main className="ws-editor-panel">

          {/* Panel topbar */}
          <div className="editor-topbar">
            <span className="editor-filename">
              {activeSidebarLabel}
              {isDirty && (
                <span className="unsaved-dot" title="Unsaved changes"> (unsaved)</span>
              )}
            </span>
            {isEditorView && (
              <span className="editor-wordcount">
                Words: {wordCount(content).toLocaleString()}
              </span>
            )}
          </div>

          {error && (
            <div className="editor-error">{error}</div>
          )}

          {/* Editor or panel content */}
          {isEditorView ? (
            loading ? (
              <div className="editor-loading">Loading...</div>
            ) : (
              <textarea
                className="editor-textarea"
                value={content}
                onChange={e => setContent(e.target.value)}
                spellCheck={false}
                autoCapitalize="off"
                autoCorrect="off"
              />
            )
          ) : (
            activePanel === 'chapters' ? (
              <ChapterList
                projectId={project.id}
                refreshKey={chaptersKey}
                onSelectChapter={setSelectedChapter}
              />
            ) : activePanel === 'continuity' ? (
              <ContinuityExplorer project={project} />
            ) : activePanel === 'qa' ? (
              <QAReportsPanel project={project} />
            ) : activePanel === 'export' ? (
              <ExportPanel project={project} />
            ) : null
          )}
        </main>
      </div>

    </div>
  );
}
