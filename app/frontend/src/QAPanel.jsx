import { useState, useEffect, useCallback } from 'react';
import {
  runLint,
  runBeatCheck,
  runContinuityCheck,
  runVoiceCheck,
  getChapterReports,
} from './api';
import './QAPanel.css';

// Report type metadata
const QA_CHECKS = [
  { key: 'LINT',       label: 'Prose Lint',   run: runLint,            scored: false },
  { key: 'BEAT_CHECK', label: 'Beat Check',   run: runBeatCheck,       scored: true  },
  { key: 'CONTINUITY', label: 'Continuity',   run: runContinuityCheck, scored: true  },
  { key: 'VOICE',      label: 'Voice Check',  run: runVoiceCheck,      scored: true  },
];

function scoreBadgeClass(score, scored) {
  if (!scored || score === 0) return 'qa-badge qa-badge-grey';
  if (score >= 80) return 'qa-badge qa-badge-green';
  if (score >= 60) return 'qa-badge qa-badge-yellow';
  return 'qa-badge qa-badge-red';
}

export default function QAPanel({ project, chapter }) {
  // reports: { LINT: QAReport|null, BEAT_CHECK: QAReport|null, ... }
  const [reports, setReports]   = useState({});
  const [running, setRunning]   = useState({});  // { key: true/false }
  const [errors, setErrors]     = useState({});   // { key: errorString }
  const [activeKey, setActiveKey] = useState(null);

  // ── Load existing reports on mount ──────────────────────────────────────
  const loadReports = useCallback(async () => {
    try {
      const list = await getChapterReports(project.id, chapter.chapter_number);
      // Keep only the most recent of each type
      const byType = {};
      for (const report of list) {
        if (!byType[report.report_type]) {
          byType[report.report_type] = report;
        }
      }
      setReports(byType);
      // Auto-open the first available report
      const firstKey = QA_CHECKS.find(c => byType[c.key])?.key;
      if (firstKey) setActiveKey(firstKey);
    } catch {
      // No reports yet — ignore
    }
  }, [project.id, chapter.chapter_number]);

  useEffect(() => {
    loadReports();
  }, [loadReports]);

  // ── Run a single check ──────────────────────────────────────────────────
  async function handleRun(check) {
    if (running[check.key]) return;
    setRunning(r => ({ ...r, [check.key]: true }));
    setErrors(e => ({ ...e, [check.key]: null }));
    try {
      const report = await check.run(project.id, chapter.chapter_number);
      setReports(r => ({ ...r, [check.key]: report }));
      setActiveKey(check.key);
    } catch (err) {
      setErrors(e => ({ ...e, [check.key]: err.message || 'Failed.' }));
    } finally {
      setRunning(r => ({ ...r, [check.key]: false }));
    }
  }

  // ── Toggle active panel ─────────────────────────────────────────────────
  function handleTabClick(key) {
    setActiveKey(prev => (prev === key ? null : key));
  }

  const activeReport = activeKey ? reports[activeKey] : null;

  return (
    <div className="qa-panel">
      <div className="qa-section-label">QA Reports</div>

      <div className="qa-buttons">
        {QA_CHECKS.map(check => {
          const report  = reports[check.key];
          const isRunning = running[check.key];
          const isActive = activeKey === check.key;
          const hasReport = !!report;

          return (
            <div key={check.key} className="qa-check-row">
              <button
                className={`qa-run-btn${isActive && hasReport ? ' qa-run-btn-active' : ''}`}
                onClick={() => {
                  if (hasReport) {
                    handleTabClick(check.key);
                  } else {
                    handleRun(check);
                  }
                }}
                disabled={isRunning}
                title={hasReport ? 'Click to toggle report' : `Run ${check.label}`}
              >
                {isRunning ? 'Running...' : check.label}
                {hasReport && check.scored && (
                  <span className={scoreBadgeClass(report.score, check.scored)}>
                    {report.score}
                  </span>
                )}
                {hasReport && !check.scored && (
                  <span className="qa-badge qa-badge-grey">done</span>
                )}
              </button>
              {hasReport && (
                <button
                  className="qa-rerun-btn"
                  onClick={() => handleRun(check)}
                  disabled={isRunning}
                  title={`Re-run ${check.label}`}
                >
                  &#8635;
                </button>
              )}
              {errors[check.key] && (
                <span className="qa-error">{errors[check.key]}</span>
              )}
            </div>
          );
        })}
      </div>

      {activeReport && (
        <div className="qa-report-panel">
          <pre className="qa-report-pre">{activeReport.report_markdown}</pre>
        </div>
      )}
    </div>
  );
}
