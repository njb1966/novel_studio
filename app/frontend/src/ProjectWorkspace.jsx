import { useState, useEffect, useCallback } from 'react';
import { getFile, saveFile, syncProject, getChapters } from './api';
import ChapterPipeline from './ChapterPipeline';
import ContinuityExplorer from './ContinuityExplorer';
import ExportPanel from './ExportPanel';
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
  { label: 'Export',      panel: 'export' },
];

const STUB_ITEMS = [
  { label: 'QA Reports', milestone: 4 },
];

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
          className="btn-primary ws-save"
          onClick={handleSave}
          disabled={!isDirty || saving}
        >
          {saving ? 'Saving...' : 'Save'}
        </button>
      </header>

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
            ) : activePanel === 'export' ? (
              <ExportPanel project={project} />
            ) : null
          )}
        </main>
      </div>

    </div>
  );
}
