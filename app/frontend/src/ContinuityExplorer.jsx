import { useState, useEffect, useCallback } from 'react';
import { getPendingFacts, getActiveFacts, approveFact, rejectFact } from './api';
import './ContinuityExplorer.css';

const FACT_TYPES = [
  'character_state',
  'object_location',
  'injury',
  'death',
  'promise',
  'mystery',
  'seed',
  'timeline',
  'world_fact',
  'relationship',
  'other',
];

// ── Fact type pill ──────────────────────────────────────────────────────────
function TypeTag({ type }) {
  return (
    <span className={`ce-type-tag ce-type-${type}`}>
      {type.replace('_', ' ')}
    </span>
  );
}

// ── Pending fact row ────────────────────────────────────────────────────────
function PendingRow({ fact, onApprove, onReject }) {
  const [flash, setFlash] = useState(null); // 'approve' | 'reject' | null

  async function handleApprove() {
    setFlash('approve');
    await onApprove(fact.id);
  }

  async function handleReject() {
    setFlash('reject');
    await onReject(fact.id);
  }

  return (
    <div className={`ce-fact-row ce-pending-row${flash ? ` ce-flash-${flash}` : ''}`}>
      <div className="ce-fact-header">
        <TypeTag type={fact.fact_type} />
        <span className="ce-fact-subject">{fact.subject}</span>
        {fact.chapter_number != null && (
          <span className="ce-fact-chapter">Ch {fact.chapter_number}</span>
        )}
      </div>
      <div className="ce-fact-text">{fact.fact}</div>
      <div className="ce-fact-actions">
        <button
          className="ce-btn-approve"
          onClick={handleApprove}
          disabled={!!flash}
        >
          Approve
        </button>
        <button
          className="ce-btn-reject"
          onClick={handleReject}
          disabled={!!flash}
        >
          Reject
        </button>
      </div>
    </div>
  );
}

// ── Active fact row ─────────────────────────────────────────────────────────
function ActiveRow({ fact }) {
  return (
    <div className="ce-fact-row">
      <div className="ce-fact-header">
        <TypeTag type={fact.fact_type} />
        <span className="ce-fact-subject">{fact.subject}</span>
        {fact.chapter_number != null && (
          <span className="ce-fact-chapter">Ch {fact.chapter_number}</span>
        )}
      </div>
      <div className="ce-fact-text">{fact.fact}</div>
    </div>
  );
}

// ── Main component ──────────────────────────────────────────────────────────
export default function ContinuityExplorer({ project }) {
  const [tab, setTab]               = useState('pending');
  const [pending, setPending]       = useState(null);
  const [active, setActive]         = useState(null);
  const [loadingPending, setLoadingPending] = useState(false);
  const [loadingActive, setLoadingActive]   = useState(false);
  const [error, setError]           = useState('');

  // Active tab filter state
  const [typeFilter, setTypeFilter] = useState('all');
  const [search, setSearch]         = useState('');

  // ── Loaders ───────────────────────────────────────────────────────────────
  const loadPending = useCallback(async () => {
    setLoadingPending(true);
    setError('');
    try {
      const data = await getPendingFacts(project.id);
      setPending(data);
    } catch (err) {
      setError(err.message || 'Failed to load pending facts.');
    } finally {
      setLoadingPending(false);
    }
  }, [project.id]);

  const loadActive = useCallback(async () => {
    setLoadingActive(true);
    setError('');
    try {
      const data = await getActiveFacts(project.id);
      setActive(data);
    } catch (err) {
      setError(err.message || 'Failed to load active facts.');
    } finally {
      setLoadingActive(false);
    }
  }, [project.id]);

  useEffect(() => {
    loadPending();
    loadActive();
  }, [loadPending, loadActive]);

  // ── Approve / reject ──────────────────────────────────────────────────────
  async function handleApprove(factId) {
    try {
      await approveFact(project.id, factId);
      // Brief delay so the flash animation is visible, then refresh both lists
      setTimeout(() => {
        loadPending();
        loadActive();
      }, 320);
    } catch (err) {
      setError(err.message || 'Approve failed.');
    }
  }

  async function handleReject(factId) {
    try {
      await rejectFact(project.id, factId);
      setTimeout(() => {
        loadPending();
      }, 320);
    } catch (err) {
      setError(err.message || 'Reject failed.');
    }
  }

  // ── Filtered active facts ─────────────────────────────────────────────────
  const filteredActive = (active || []).filter(f => {
    if (typeFilter !== 'all' && f.fact_type !== typeFilter) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        f.subject.toLowerCase().includes(q) ||
        f.fact.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const pendingCount = pending ? pending.length : 0;

  return (
    <div className="ce-explorer">

      {/* Tab bar */}
      <div className="ce-tabs">
        <button
          className={`ce-tab${tab === 'pending' ? ' ce-tab-active' : ''}`}
          onClick={() => setTab('pending')}
        >
          Pending Approval
          {pendingCount > 0 && (
            <span className="ce-tab-badge">{pendingCount}</span>
          )}
        </button>
        <button
          className={`ce-tab${tab === 'active' ? ' ce-tab-active' : ''}`}
          onClick={() => setTab('active')}
        >
          Active Facts
          {active && (
            <span className="ce-tab-count">{active.length}</span>
          )}
        </button>
      </div>

      {error && <div className="ce-error">{error}</div>}

      {/* Pending tab */}
      {tab === 'pending' && (
        <div className="ce-tab-content">
          {loadingPending ? (
            <div className="ce-state">Loading...</div>
          ) : !pending || pending.length === 0 ? (
            <div className="ce-state ce-state-empty">
              No facts pending approval.
            </div>
          ) : (
            <div className="ce-fact-list">
              {pending.map(f => (
                <PendingRow
                  key={f.id}
                  fact={f}
                  onApprove={handleApprove}
                  onReject={handleReject}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Active tab */}
      {tab === 'active' && (
        <div className="ce-tab-content">
          <div className="ce-filters">
            <select
              className="ce-filter-select"
              value={typeFilter}
              onChange={e => setTypeFilter(e.target.value)}
            >
              <option value="all">All types</option>
              {FACT_TYPES.map(t => (
                <option key={t} value={t}>{t.replace('_', ' ')}</option>
              ))}
            </select>
            <input
              className="ce-filter-search"
              type="text"
              placeholder="Search..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>

          {loadingActive ? (
            <div className="ce-state">Loading...</div>
          ) : filteredActive.length === 0 ? (
            <div className="ce-state ce-state-empty">
              {active && active.length === 0
                ? 'No active facts yet. Approve some pending facts to get started.'
                : 'No facts match the current filter.'}
            </div>
          ) : (
            <div className="ce-fact-list">
              {filteredActive.map(f => (
                <ActiveRow key={f.id} fact={f} />
              ))}
            </div>
          )}
        </div>
      )}

    </div>
  );
}
