import { useState, useEffect, useCallback } from 'react';
import { exportManuscript, getExportStatus } from './api';
import './ExportPanel.css';

function formatDate(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

export default function ExportPanel({ project }) {
  const [status, setStatus]               = useState(null);
  const [loadError, setLoadError]         = useState('');
  const [includeHeadings, setIncludeHeadings] = useState(true);
  const [includeSummaries, setIncludeSummaries] = useState(false);
  const [exporting, setExporting]         = useState(false);
  const [exportResult, setExportResult]   = useState(null);
  const [exportError, setExportError]     = useState('');
  const [copied, setCopied]               = useState(false);

  const loadStatus = useCallback(async () => {
    setLoadError('');
    try {
      const data = await getExportStatus(project.id);
      setStatus(data);
    } catch (err) {
      setLoadError(err.message);
    }
  }, [project.id]);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  async function handleExport() {
    if (exporting) return;
    setExporting(true);
    setExportError('');
    setExportResult(null);
    try {
      const result = await exportManuscript(project.id, {
        include_chapter_headings: includeHeadings,
        include_summaries: includeSummaries,
      });
      setExportResult(result);
      // Refresh status to show updated word count + timestamp
      await loadStatus();
    } catch (err) {
      setExportError(err.message);
    } finally {
      setExporting(false);
    }
  }

  async function handleCopyPath() {
    const path = exportResult?.absolute_path || status?.absolute_path || '';
    if (!path) return;
    try {
      await navigator.clipboard.writeText(path);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      // Clipboard API unavailable — silently ignore
    }
  }

  const approvedCount = status?.approved_chapters ?? 0;
  const totalCount    = status?.total_chapters ?? 0;
  const canExport     = approvedCount > 0 && !exporting;

  const displayPath = exportResult?.absolute_path || (status?.exists ? status.absolute_path : '');

  return (
    <div className="ep-panel">
      <div className="ep-header">
        <h2 className="ep-title">Export Manuscript</h2>
      </div>

      <div className="ep-body">

        {/* Status section */}
        <section className="ep-section">
          <div className="ep-section-label">Status</div>
          {loadError ? (
            <div className="ep-error">{loadError}</div>
          ) : status === null ? (
            <div className="ep-dim">Loading...</div>
          ) : (
            <div className="ep-status-grid">
              <div className="ep-status-row">
                <span className="ep-status-key">Approved chapters</span>
                <span className="ep-status-val">
                  {approvedCount} / {totalCount}
                </span>
              </div>
              <div className="ep-status-row">
                <span className="ep-status-key">Last export</span>
                <span className="ep-status-val">
                  {status.exists
                    ? `${formatDate(status.modified_at)}  (${status.word_count.toLocaleString()} words)`
                    : <span className="ep-dim">Not yet exported</span>
                  }
                </span>
              </div>
            </div>
          )}
        </section>

        {/* Options section */}
        <section className="ep-section">
          <div className="ep-section-label">Options</div>
          <label className="ep-checkbox-row">
            <input
              type="checkbox"
              checked={includeHeadings}
              onChange={e => setIncludeHeadings(e.target.checked)}
            />
            Include chapter headings
          </label>
          <label className="ep-checkbox-row">
            <input
              type="checkbox"
              checked={includeSummaries}
              onChange={e => setIncludeSummaries(e.target.checked)}
            />
            Include summaries after each chapter
          </label>
        </section>

        {/* Export button */}
        <section className="ep-section ep-action-row">
          <button
            className="ep-btn-export btn-primary"
            onClick={handleExport}
            disabled={!canExport}
            title={approvedCount === 0 ? 'No approved chapters to export' : undefined}
          >
            {exporting ? 'Exporting...' : 'Export Approved Chapters'}
          </button>
          {approvedCount === 0 && !exporting && (
            <span className="ep-dim ep-hint">
              Approve at least one chapter before exporting.
            </span>
          )}
        </section>

        {/* Success banner */}
        {exportResult && !exportError && (
          <div className="ep-success-banner">
            Exported successfully — {exportResult.chapter_count} chapter{exportResult.chapter_count !== 1 ? 's' : ''},
            {' '}{exportResult.word_count.toLocaleString()} words
          </div>
        )}

        {/* Export error */}
        {exportError && (
          <div className="ep-error ep-error-banner">{exportError}</div>
        )}

        {/* Output file */}
        {displayPath && (
          <>
            <div className="ep-divider" />
            <section className="ep-section">
              <div className="ep-section-label">Output file</div>
              <div className="ep-path-row">
                <code className="ep-path">{displayPath}</code>
                <button
                  className="ep-btn-copy btn-secondary"
                  onClick={handleCopyPath}
                >
                  {copied ? 'Copied' : 'Copy Path'}
                </button>
              </div>
            </section>
          </>
        )}

        {/* After export hint */}
        <div className="ep-divider" />
        <section className="ep-section">
          <div className="ep-section-label">After export</div>
          <p className="ep-hint-text">
            Open the file in your text editor or Markdown viewer to review the
            manuscript. The output is plain Markdown — paste it into Pandoc,
            Obsidian, or any editor that reads .md files.
          </p>
        </section>

      </div>
    </div>
  );
}
