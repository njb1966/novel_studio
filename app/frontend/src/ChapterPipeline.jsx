import { useState, useEffect, useCallback } from 'react';
import { getDraft, generateDraft, saveDraft, extractFacts, generateSummary, getSummary, approveChapter } from './api';
import QAPanel from './QAPanel';
import './ChapterPipeline.css';

function wordCount(text) {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

export default function ChapterPipeline({ project, chapter, onBack, onOpenContinuity }) {
  const [draft, setDraft]           = useState('');
  const [savedDraft, setSavedDraft] = useState('');
  const [loadingDraft, setLoadingDraft] = useState(true);

  const [generating, setGenerating] = useState(false);
  const [genError, setGenError]     = useState('');

  const [saving, setSaving] = useState(false);

  const [extracting, setExtracting]         = useState(false);
  const [extractError, setExtractError]     = useState('');
  const [extractedCount, setExtractedCount] = useState(null);  // null = not yet run

  // ── Summary state ──────────────────────────────────────────────────────────
  const [summary, setSummary]           = useState('');
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState('');

  // ── Approve state ──────────────────────────────────────────────────────────
  const [chapterStatus, setChapterStatus] = useState(chapter.status || 'draft');
  const [approving, setApproving]         = useState(false);
  const [approveError, setApproveError]   = useState('');
  const [approveSuccess, setApproveSuccess] = useState('');

  const isDirty = draft !== savedDraft;
  const wc      = wordCount(draft);

  // ── Load existing draft on mount ────────────────────────────────────────
  const loadDraft = useCallback(async () => {
    setLoadingDraft(true);
    try {
      const data = await getDraft(project.id, chapter.chapter_number);
      setDraft(data.content || '');
      setSavedDraft(data.content || '');
    } catch {
      // No draft yet is fine
      setDraft('');
      setSavedDraft('');
    } finally {
      setLoadingDraft(false);
    }
  }, [project.id, chapter.chapter_number]);

  // ── Load existing summary on mount ───────────────────────────────────────
  const loadSummary = useCallback(async () => {
    try {
      const data = await getSummary(project.id, chapter.chapter_number);
      setSummary(data.summary || '');
    } catch {
      setSummary('');
    }
  }, [project.id, chapter.chapter_number]);

  useEffect(() => {
    loadDraft();
    loadSummary();
  }, [loadDraft, loadSummary]);

  // ── Generate ─────────────────────────────────────────────────────────────
  async function handleGenerate() {
    if (generating) return;
    setGenerating(true);
    setGenError('');
    try {
      const result = await generateDraft(project.id, chapter.chapter_number);
      const prose = result.content || '';
      setDraft(prose);
      setSavedDraft(prose);
    } catch (err) {
      setGenError(err.message || 'Generation failed.');
    } finally {
      setGenerating(false);
    }
  }

  // ── Save ──────────────────────────────────────────────────────────────────
  async function handleSave() {
    if (!isDirty || saving) return;
    setSaving(true);
    try {
      await saveDraft(project.id, chapter.chapter_number, draft);
      setSavedDraft(draft);
    } catch (err) {
      // Surface error in the topbar briefly
      console.error('Save failed:', err);
    } finally {
      setSaving(false);
    }
  }

  // ── Extract facts ─────────────────────────────────────────────────────────
  async function handleExtractFacts() {
    if (extracting) return;
    setExtracting(true);
    setExtractError('');
    setExtractedCount(null);
    try {
      const facts = await extractFacts(project.id, chapter.chapter_number);
      setExtractedCount(facts.length);
    } catch (err) {
      setExtractError(err.message || 'Extraction failed.');
    } finally {
      setExtracting(false);
    }
  }

  // ── Generate summary ──────────────────────────────────────────────────────
  async function handleGenerateSummary() {
    if (summaryLoading) return;
    setSummaryLoading(true);
    setSummaryError('');
    try {
      const result = await generateSummary(project.id, chapter.chapter_number);
      setSummary(result.summary || '');
    } catch (err) {
      setSummaryError(err.message || 'Summary generation failed.');
    } finally {
      setSummaryLoading(false);
    }
  }

  // ── Approve chapter ───────────────────────────────────────────────────────
  async function handleApprove() {
    if (approving) return;
    const ok = window.confirm(
      `Approve Chapter ${chapter.chapter_number}? This will copy the current draft to final. Are you sure?`
    );
    if (!ok) return;
    setApproving(true);
    setApproveError('');
    setApproveSuccess('');
    try {
      const result = await approveChapter(project.id, chapter.chapter_number);
      setChapterStatus(result.status);
      setApproveSuccess(`Final saved to ${result.final_path}`);
    } catch (err) {
      setApproveError(err.message || 'Approval failed.');
    } finally {
      setApproving(false);
    }
  }

  // ── Back guard ────────────────────────────────────────────────────────────
  function handleBack() {
    if (isDirty) {
      const ok = window.confirm('You have unsaved changes. Go back anyway?');
      if (!ok) return;
    }
    onBack();
  }

  const chapterLabel = `Chapter ${chapter.chapter_number}${chapter.title ? ` — ${chapter.title}` : ''}`;

  return (
    <div className="chapter-pipeline">

      {/* Header */}
      <header className="cp-header">
        <button className="cp-back" onClick={handleBack}>
          &#8592; Chapters
        </button>
        <span className="cp-heading">{chapterLabel}</span>
        {chapter.pov_character && (
          <span className="cp-pov-tag">POV: {chapter.pov_character}</span>
        )}
        <span className={`cp-status-badge cp-status-${chapterStatus}`}>
          {chapterStatus}
        </span>
      </header>

      <div className="cp-body">

        {/* Left panel — outline + actions */}
        <aside className="cp-left">

          <div className="cp-section-label">Outline</div>

          {chapter.outline_goal ? (
            <div className="cp-outline-field">
              <strong>Goal:</strong> {chapter.outline_goal}
            </div>
          ) : (
            <div className="cp-outline-empty">No goal recorded.</div>
          )}

          {chapter.outline_conflict && (
            <div className="cp-outline-field">
              <strong>Conflict:</strong> {chapter.outline_conflict}
            </div>
          )}

          {chapter.outline_revelation && (
            <div className="cp-outline-field">
              <strong>Revelation:</strong> {chapter.outline_revelation}
            </div>
          )}

          {chapter.outline_notes && (
            <div className="cp-outline-field">
              <strong>Notes:</strong> {chapter.outline_notes}
            </div>
          )}

          <div className="cp-divider" />

          <div className="cp-section-label">Pipeline</div>

          <button
            className="cp-btn-generate"
            onClick={handleGenerate}
            disabled={generating || chapterStatus === 'approved'}
            title={chapterStatus === 'approved' ? 'Chapter is locked (approved)' : undefined}
          >
            {generating ? 'Generating...' : 'Generate Draft'}
          </button>

          {genError && (
            <div className="cp-generate-error">{genError}</div>
          )}

          <div className="cp-divider" />

          <QAPanel project={project} chapter={chapter} />

          <div className="cp-divider" />

          <div className="cp-section-label">Continuity</div>

          <button
            className="cp-btn-extract"
            onClick={handleExtractFacts}
            disabled={extracting}
          >
            {extracting ? 'Extracting...' : 'Extract New Facts'}
          </button>

          {extractError && (
            <div className="cp-generate-error">{extractError}</div>
          )}

          {extractedCount !== null && !extractError && (
            <div className="cp-extract-result">
              {extractedCount === 0
                ? 'No new facts found.'
                : `${extractedCount} fact${extractedCount !== 1 ? 's' : ''} added to pending.`}
              {extractedCount > 0 && onOpenContinuity && (
                <button
                  className="cp-continuity-link"
                  onClick={onOpenContinuity}
                >
                  Review in Continuity
                </button>
              )}
            </div>
          )}

          <div className="cp-divider" />

          <div className="cp-section-label">Final Steps</div>

          {/* Generate Summary */}
          <button
            className="cp-btn-action"
            onClick={handleGenerateSummary}
            disabled={summaryLoading || !draft || chapterStatus === 'approved'}
            title={!draft ? 'Generate a draft first' : undefined}
          >
            {summaryLoading ? 'Generating...' : summary ? 'Regenerate Summary' : 'Generate Summary'}
          </button>

          {summaryError && (
            <div className="cp-generate-error">{summaryError}</div>
          )}

          {summary && (
            <div className="cp-summary-box">
              {summary}
            </div>
          )}

          {/* Approve Chapter */}
          {approveSuccess ? (
            <div className="cp-approve-success">
              Chapter approved<br />
              <span className="cp-approve-path">{approveSuccess}</span>
            </div>
          ) : (
            <button
              className="cp-btn-approve"
              onClick={handleApprove}
              disabled={approving || !draft || !summary || chapterStatus === 'approved'}
              title={
                chapterStatus === 'approved' ? 'Already approved' :
                !draft ? 'No draft' :
                !summary ? 'Generate a summary first' :
                undefined
              }
            >
              {approving ? 'Approving...' : 'Approve Chapter'}
            </button>
          )}

          {approveError && (
            <div className="cp-generate-error">{approveError}</div>
          )}

        </aside>

        {/* Right panel — draft editor */}
        <section className="cp-right">

          <div className="cp-editor-topbar">
            <span className="cp-wordcount">
              {wc.toLocaleString()} words
              {isDirty && <span className="cp-unsaved"> (unsaved)</span>}
            </span>
            <button
              className="cp-save-btn"
              onClick={handleSave}
              disabled={!isDirty || saving}
            >
              {saving ? 'Saving...' : 'Save Draft'}
            </button>
          </div>

          {loadingDraft ? (
            <div className="cp-loading">Loading draft...</div>
          ) : (
            <textarea
              className="cp-textarea"
              value={draft}
              onChange={e => setDraft(e.target.value)}
              placeholder="No draft yet. Click Generate Draft to begin."
              spellCheck={false}
              autoCapitalize="off"
              autoCorrect="off"
            />
          )}

          {/* Overlay while generating */}
          {generating && (
            <div className="cp-generating-overlay">
              <div className="cp-spinner" />
              <span className="cp-generating-label">Generating chapter draft...</span>
            </div>
          )}

        </section>

      </div>
    </div>
  );
}
