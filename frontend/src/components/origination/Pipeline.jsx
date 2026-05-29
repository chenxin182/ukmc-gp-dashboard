import { useEffect, useState, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { getDeals } from '../../api';
import {
  STAGES, StageBadge, UrgencyBadge, ScoreBar,
  CountryFlag, fmtSize, fmtDate, Card, Spinner, Empty
} from './shared';

// ─── Filters bar ─────────────────────────────────────────────────────────────

function FiltersBar({ filters, onChange }) {
  const COUNTRIES = ['','Indonesia','Vietnam','Malaysia','Thailand','Philippines','Singapore','Hong Kong','UAE','China'];
  const SECTORS   = ['','Telecom','Data Centers','Mining / Nickel','Smelting','Renewable Energy','Power / Energy','Logistics / Ports','Infrastructure','Fiber Optic / Subsea Cable'];
  const URGENCIES = ['','HIGH','MEDIUM','LOW'];
  const STAGES_F  = ['', ...STAGES.map(s => s.key)];

  const sel = (name, opts, label) => (
    <select
      className="bg-slate-800 border border-slate-700 text-slate-300 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-ukmc-500"
      value={filters[name]}
      onChange={e => onChange(name, e.target.value)}
    >
      {opts.map(o => <option key={o} value={o}>{o || label}</option>)}
    </select>
  );

  return (
    <div className="flex flex-wrap items-center gap-2">
      <input
        type="text"
        placeholder="Search company / sector…"
        className="bg-slate-800 border border-slate-700 text-slate-300 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-ukmc-500 flex-1 min-w-0"
        value={filters.q}
        onChange={e => onChange('q', e.target.value)}
      />
      {sel('stage',   STAGES_F,   'All Stages')}
      {sel('country', COUNTRIES,  'All Countries')}
      {sel('urgency', URGENCIES,  'All Urgency')}
      {sel('sector',  SECTORS,    'All Sectors')}
      <select
        className="bg-slate-800 border border-slate-700 text-slate-300 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-ukmc-500"
        value={filters.sort}
        onChange={e => onChange('sort', e.target.value)}
      >
        <option value="score">Sort: Fit Score</option>
        <option value="updated">Sort: Last Updated</option>
        <option value="size">Sort: Deal Size</option>
        <option value="urgency">Sort: Urgency</option>
      </select>
    </div>
  );
}

// ─── Deal card ────────────────────────────────────────────────────────────────

function DealCard({ deal }) {
  const navigate = useNavigate();
  return (
    <div
      className="bg-slate-800 border border-slate-700 rounded-xl p-4 hover:border-ukmc-500/50 hover:bg-slate-750 cursor-pointer transition-all group"
      onClick={() => navigate(`/origination/deals/${deal.id}`)}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="min-w-0">
          <div className="flex items-center gap-1.5">
            <CountryFlag country={deal.country} />
            <h3 className="font-semibold text-slate-100 text-sm truncate group-hover:text-ukmc-300 transition-colors">
              {deal.company_name}
            </h3>
            {deal.priority === 'HIGH' && <span className="text-red-400 text-xs">🔴</span>}
            {deal.dim_sum_feasible && <span className="text-amber-400 text-xs" title="Dim Sum Feasible">🏮</span>}
          </div>
          <p className="text-xs text-slate-500 mt-0.5">{deal.sector} · {deal.country}</p>
        </div>
        <UrgencyBadge urgency={deal.urgency} />
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-500">Type</span>
          <span className="text-xs text-slate-300 text-right max-w-32 truncate">{deal.financing_type || '—'}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-500">Size</span>
          <span className="text-xs font-mono text-amber-300">{fmtSize(deal.estimated_size_mn)}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-500">Purpose</span>
          <span className="text-xs text-slate-400 max-w-32 truncate text-right">{deal.purpose || '—'}</span>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-slate-700">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs text-slate-500">UKMC Fit</span>
          <StageBadge stage={deal.stage} />
        </div>
        <ScoreBar score={deal.ukmc_fit_score} size="sm" />
      </div>

      {deal.next_action && (
        <div className="mt-2">
          <p className="text-xs text-slate-500">Next: <span className="text-ukmc-300">{deal.next_action}</span></p>
        </div>
      )}
    </div>
  );
}

// ─── Kanban column ───────────────────────────────────────────────────────────

function KanbanColumn({ stage, deals }) {
  const total = deals.reduce((s, d) => s + (d.estimated_size_mn || 0), 0);
  return (
    <div className="flex-shrink-0 w-72">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full`} style={{ background: stage.color.includes('indigo') ? '#6366f1' : stage.color.includes('violet') ? '#8b5cf6' : stage.color.includes('sky') ? '#0ea5e9' : stage.color.includes('amber') ? '#f59e0b' : stage.color.includes('orange') ? '#f97316' : stage.color.includes('emerald') ? '#10b981' : '#6b7280' }} />
          <span className="text-sm font-medium text-slate-300">{stage.label}</span>
          <span className="bg-slate-700 text-slate-400 text-xs rounded-full px-1.5 py-0.5">{deals.length}</span>
        </div>
        {total > 0 && (
          <span className="text-xs text-amber-400 font-mono">{fmtSize(total)}</span>
        )}
      </div>
      <div className="space-y-3 min-h-16">
        {deals.map(d => <DealCard key={d.id} deal={d} />)}
        {deals.length === 0 && (
          <div className="border-2 border-dashed border-slate-700 rounded-xl p-4 text-center">
            <p className="text-xs text-slate-600">No deals</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Pipeline Page ────────────────────────────────────────────────────────────

export default function Pipeline() {
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState('');
  const [view, setView]     = useState('list'); // 'list' | 'kanban'
  const [filters, setFilters] = useState({
    q: '', stage: '', country: '', sector: '', urgency: '', sort: 'score',
  });

  const setFilter = useCallback((key, val) => {
    setFilters(f => ({ ...f, [key]: val }));
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = { ...filters, is_active: true, limit: 100 };
      const res = await getDeals(params);
      setDeals(res.deals || res);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { load(); }, [load]);

  const navigate = useNavigate();

  // Group by stage for Kanban
  const grouped = {};
  STAGES.slice(0, 6).forEach(s => {
    grouped[s.key] = deals.filter(d => d.stage === s.key);
  });

  const totalPipeline = deals.reduce((s, d) => s + (d.estimated_size_mn || 0), 0);

  return (
    <div className="space-y-5 animate-fade-in">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Deal Pipeline</h1>
          <p className="text-slate-400 text-sm mt-0.5">
            {deals.length} deals · {fmtSize(totalPipeline)} total pipeline
          </p>
        </div>
        <div className="flex gap-2">
          {/* View toggle */}
          <div className="flex bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
            <button
              onClick={() => setView('list')}
              className={`px-3 py-1.5 text-sm transition-colors ${view === 'list' ? 'bg-ukmc-700 text-white' : 'text-slate-400 hover:text-slate-200'}`}
            >
              ≡ List
            </button>
            <button
              onClick={() => setView('kanban')}
              className={`px-3 py-1.5 text-sm transition-colors ${view === 'kanban' ? 'bg-ukmc-700 text-white' : 'text-slate-400 hover:text-slate-200'}`}
            >
              ⊞ Kanban
            </button>
          </div>
          <Link
            to="/origination/new-deal"
            className="px-3 py-1.5 text-sm bg-ukmc-600 hover:bg-ukmc-500 text-white rounded-lg transition-colors"
          >
            + New Deal
          </Link>
        </div>
      </div>

      {/* Filters */}
      <FiltersBar filters={filters} onChange={setFilter} />

      {/* Content */}
      {loading ? (
        <div className="flex justify-center py-20"><Spinner /></div>
      ) : error ? (
        <div className="text-center py-10 text-red-400">{error}</div>
      ) : deals.length === 0 ? (
        <Empty icon="🎯" title="No deals match filters" subtitle="Adjust your filters or add a new deal." />
      ) : view === 'kanban' ? (
        /* Kanban */
        <div className="overflow-x-auto pb-4">
          <div className="flex gap-4 min-w-max">
            {STAGES.slice(0, 6).map(stage => (
              <KanbanColumn key={stage.key} stage={stage} deals={grouped[stage.key] || []} />
            ))}
          </div>
        </div>
      ) : (
        /* List */
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  {['Company','Country','Sector','Type','Size','Stage','Fit','Urgency','Updated'].map(h => (
                    <th key={h} className="text-left px-4 py-2.5 text-xs font-medium text-slate-500 uppercase whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {deals.map(d => (
                  <tr
                    key={d.id}
                    onClick={() => navigate(`/origination/deals/${d.id}`)}
                    className="border-b border-slate-700/40 hover:bg-slate-700/30 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        {d.priority === 'HIGH' && <span className="text-red-400 text-xs">🔴</span>}
                        <span className="text-sm font-medium text-slate-200">{d.company_name}</span>
                        {d.dim_sum_feasible && <span className="text-amber-400 text-xs" title="Dim Sum Feasible">🏮</span>}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <CountryFlag country={d.country} />
                        <span className="text-xs text-slate-400">{d.country}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">{d.sector}</td>
                    <td className="px-4 py-3 text-xs text-slate-400 max-w-32 truncate">{d.financing_type}</td>
                    <td className="px-4 py-3 text-xs font-mono text-amber-300 whitespace-nowrap">{fmtSize(d.estimated_size_mn)}</td>
                    <td className="px-4 py-3"><StageBadge stage={d.stage} /></td>
                    <td className="px-4 py-3 w-28"><ScoreBar score={d.ukmc_fit_score} size="sm" /></td>
                    <td className="px-4 py-3"><UrgencyBadge urgency={d.urgency} /></td>
                    <td className="px-4 py-3 text-xs text-slate-500 whitespace-nowrap">{fmtDate(d.updated_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
