import { useState, useEffect } from 'react';
import { getProjectQA } from './api';
import './QAReportsPanel.css';

const TYPE_LABELS = {
  lint:              'Prose Lint',
  beat_check:        'Beat Check',
  continuity_check:  'Continuity',
  voice_check:       'Voice Check',
};

const ALL_TYPES = ['all', 'lint', 'beat_check', 'continuity_check', 'voice_check'];

function scoreClass(score, type) {
  if (type === 'lint' || score === 0) return 'score-grey';
  if (score >= 80) return 'score-green';
  if (score >= 60) return 'score-yellow';
  return 'score-red';
}

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

export default function QAReportsPanel({ project }) {
  const [reports, setReports]     = useState(null);
  const [error, setError]         = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterChapter, setFilterChapter] = useState('all');
  const [expanded, setExpanded]   = useState(null); // report id

  useEffect(() => {
    let cancelled = false;
    getProjectQA(project.id)
      .then(data => { if (!cancelled) setReports(data); })
      .catch(err  => { if (!cancelled) setError(err.message); });
    return () => { cancelled = true; };
  }, [project.id]);

  if (error) return <div className="qarp-empty">Error loading reports: {error}</div>;
  if (reports === null) return <div className="qarp-empty">Loading...</div>;
  if (reports.length === 0) return (
    <div className="qarp-empty">
      No QA reports yet.<br />
      Open a chapter and run Prose Lint, Beat Check, Continuity Check, or Voice Check.
    </div>
  );

  // Build chapter options from reports
  const chapters = ['all', ...Array.from(
    new Set(reports.map(r => r.chapter_number).filter(Boolean).sort((a, b) => a - b))
  )];

  const visible = reports.filter(r => {
    if (filterType    !== 'all' && r.report_type    !== filterType) return false;
    if (filterChapter !== 'all' && r.chapter_number !== Number(filterChapter)) return false;
    return true;
  });

  // Group by chapter for display
  const grouped = visible.reduce((acc, r) => {
    const key = r.chapter_number || 0;
    if (!acc[key]) acc[key] = [];
    acc[key].push(r);
    return acc;
  }, {});

  const sortedChapterKeys = Object.keys(grouped)
    .map(Number)
    .sort((a, b) => a - b);

  return (
    <div className="qarp">
      <div className="qarp-toolbar">
        <label className="qarp-filter-label">
          Type
          <select value={filterType} onChange={e => setFilterType(e.target.value)}>
            {ALL_TYPES.map(t => (
              <option key={t} value={t}>{t === 'all' ? 'All types' : TYPE_LABELS[t] || t}</option>
            ))}
          </select>
        </label>
        <label className="qarp-filter-label">
          Chapter
          <select value={filterChapter} onChange={e => setFilterChapter(e.target.value)}>
            {chapters.map(c => (
              <option key={c} value={c}>{c === 'all' ? 'All chapters' : `Chapter ${c}`}</option>
            ))}
          </select>
        </label>
        <span className="qarp-count">{visible.length} report{visible.length !== 1 ? 's' : ''}</span>
      </div>

      <div className="qarp-list">
        {sortedChapterKeys.map(chNum => (
          <div key={chNum} className="qarp-chapter-group">
            <div className="qarp-chapter-heading">
              {chNum > 0 ? `Chapter ${chNum}` : 'No chapter'}
            </div>
            {grouped[chNum].map(r => (
              <div key={r.id} className="qarp-row">
                <div
                  className="qarp-row-header"
                  onClick={() => setExpanded(expanded === r.id ? null : r.id)}
                >
                  <span className="qarp-type-badge">
                    {TYPE_LABELS[r.report_type] || r.report_type}
                  </span>
                  <span className={`qarp-score ${scoreClass(r.score, r.report_type)}`}>
                    {r.report_type === 'lint' ? 'lint' : (r.score > 0 ? r.score : '—')}
                  </span>
                  <span className="qarp-date">{formatDate(r.created_at)}</span>
                  <span className="qarp-toggle">{expanded === r.id ? '▲' : '▼'}</span>
                </div>
                {expanded === r.id && (
                  <div className="qarp-report-body">
                    <pre className="qarp-report-text">{r.report_markdown}</pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
