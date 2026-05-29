import { useEffect, useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { getPipelineStats, getSignals, getDeals } from '../../api';
import {
  StatCard, Card, Spinner, Empty, StageBadge, UrgencyBadge,
  ScoreBar, CountryFlag, fmtSize, fmtDate
} from './shared';

// ─── Sector color palette ────────────────────────────────────────────────────

const SECTOR_COLORS = [
  '#0ea5e9','#f59e0b','#10b981','#8b5cf6','#f97316',
  '#06b6d4','#a3e635','#ec4899','#6366f1','#14b8a6',
];

// ─── Stage funnel order ──────────────────────────────────────────────────────

const STAGE_ORDER = ['DISCOVERY','RESEARCH','ANALYSIS','OUTREACH','PROPOSAL','MANDATE'];

// ─── Mini deal row ───────────────────────────────────────────────────────────

function DealRow({ deal }) {
  const navigate = useNavigate();
  return (
    <tr
      className="border-b border-slate-700/50 hover:bg-slate-700/30 cursor-pointer transition-colors"
      onClick={() => navigate(`/origination/deals/${deal.id}`)}
    >
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <CountryFlag country={deal.country} />
          <div>
            <p className="text-sm font-medium text-slate-200 leading-tight">{deal.company_name}</p>
            <p className="text-xs text-slate-500">{deal.sector}</p>
          </div>
        </div>
      </td>
      <td className="px-4 py-3 hidden sm:table-cell">
        <span className="text-xs text-slate-400">{deal.financing_type || '—'}</span>
      </td>
      <td className="px-4 py-3 text-right hidden md:table-cell">
        <span className="text-sm font-mono text-amber-300">{fmtSize(deal.estimated_size_mn)}</span>
      </td>
      <td className="px-4 py-3">
        <StageBadge stage={deal.stage} />
      </td>
      <td className="px-4 py-3 hidden lg:table-cell">
        <ScoreBar score={deal.ukmc_fit_score} size="sm" />
      </td>
      <td className="px-4 py-3">
        <UrgencyBadge urgency={deal.urgency} />
      </td>
    </tr>
  );
}

// ─── Signal row ──────────────────────────────────────────────────────────────

function SignalRow({ signal }) {
  const urgencyColor = {
    HIGH:   'border-l-red-500 bg-red-500/5',
    MEDIUM: 'border-l-amber-500 bg-amber-500/5',
    LOW:    'border-l-blue-500 bg-blue-500/5',
  }[signal.urgency] || 'border-l-slate-500';

  return (
    <div className={`border-l-2 pl-3 py-2 rounded-r ${urgencyColor}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-200 truncate">{signal.headline}</p>
          <p className="text-xs text-slate-500 mt-0.5">
            <CountryFlag country={signal.country} />
            {' '}{signal.company_name} · {signal.sector}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <UrgencyBadge urgency={signal.urgency} />
          <span className="text-xs text-slate-600">{fmtDate(signal.detected_at)}</span>
        </div>
      </div>
      {signal.financing_implied_mn && (
        <p className="text-xs text-amber-400 mt-1">
          💰 Implied: {fmtSize(signal.financing_implied_mn)}
        </p>
      )}
    </div>
  );
}

// ─── Main Dashboard ──────────────────────────────────────────────────────────

export default function DealDashboard() {
  const [stats, setStats]     = useState(null);
  const [signals, setSignals] = useState([]);
  const [topDeals, setTopDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [s, sig, deals] = await Promise.all([
        getPipelineStats(),
        getSignals({ limit: 8, reviewed: false }),
        getDeals({ sort: 'score', limit: 10, is_active: true }),
      ]);
      setStats(s);
      setSignals(sig.signals || sig);
      setTopDeals(deals.deals || deals);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Spinner size="lg" />
          <p className="text-slate-400 mt-3 text-sm">Loading intelligence data…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <span className="text-4xl">⚠️</span>
          <p className="text-red-400 mt-2">{error}</p>
          <button onClick={load} className="mt-4 text-sm text-ukmc-400 underline">Retry</button>
        </div>
      </div>
    );
  }

  const stageData = stats?.by_stage
    ? STAGE_ORDER.map(s => ({ name: s, count: stats.by_stage[s] || 0 }))
    : [];

  const sectorData = stats?.by_sector
    ? Object.entries(stats.by_sector).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([k, v]) => ({ name: k, value: v }))
    : [];

  const countryData = stats?.by_country
    ? Object.entries(stats.by_country).sort((a, b) => b[1] - a[1]).slice(0, 6).map(([k, v]) => ({ name: k, value: v }))
    : [];

  const totalPipelineBn = ((stats?.total_pipeline_mn || 0) / 1000).toFixed(1);

  return (
    <div className="space-y-6 animate-fade-in">

      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Deal Origination</h1>
          <p className="text-slate-400 text-sm mt-0.5">
            UKMC International · Asia-Pacific Intelligence Dashboard
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            to="/origination/intelligence"
            className="px-3 py-2 text-sm bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg transition-colors border border-slate-600"
          >
            🔍 Intelligence Feed
          </Link>
          <Link
            to="/origination/new-deal"
            className="px-3 py-2 text-sm bg-ukmc-600 hover:bg-ukmc-500 text-white rounded-lg transition-colors"
          >
            + New Deal
          </Link>
        </div>
      </div>

      {/* ── KPI Row ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Active Deals"
          value={stats?.active_deals ?? 0}
          sub={`${stats?.high_urgency ?? 0} high urgency`}
          icon="🎯"
          accent="text-ukmc-400"
        />
        <StatCard
          label="Pipeline Value"
          value={`USD ${totalPipelineBn}B`}
          sub={`${stats?.total_deals ?? 0} total opportunities`}
          icon="💰"
          accent="text-amber-400"
        />
        <StatCard
          label="Mandate Stage"
          value={stats?.by_stage?.MANDATE ?? 0}
          sub={`${stats?.by_stage?.PROPOSAL ?? 0} in proposal`}
          icon="📋"
          accent="text-emerald-400"
        />
        <StatCard
          label="New Signals"
          value={stats?.unreviewed_signals ?? 0}
          sub="pending review"
          icon="📡"
          accent="text-purple-400"
        />
      </div>

      {/* ── Charts Row ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

        {/* Stage Funnel */}
        <Card title="Pipeline Funnel" className="md:col-span-2">
          <div className="p-4">
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={stageData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <XAxis
                  dataKey="name"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  allowDecimals={false}
                />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                  labelStyle={{ color: '#cbd5e1' }}
                  itemStyle={{ color: '#38bdf8' }}
                />
                <Bar dataKey="count" fill="#0c86e8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Sector Pie */}
        <Card title="By Sector">
          <div className="p-4">
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie
                  data={sectorData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={75}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {sectorData.map((_, i) => (
                    <Cell key={i} fill={SECTOR_COLORS[i % SECTOR_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                  labelStyle={{ color: '#cbd5e1' }}
                  itemStyle={{ color: '#94a3b8' }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-1 mt-1">
              {sectorData.slice(0, 4).map((s, i) => (
                <div key={s.name} className="flex items-center gap-2 text-xs">
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ background: SECTOR_COLORS[i] }} />
                  <span className="text-slate-400 truncate flex-1">{s.name}</span>
                  <span className="text-slate-300 font-mono">{s.value}</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      {/* ── Country breakdown ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card title="Top Countries">
          <div className="divide-y divide-slate-700/50">
            {countryData.map((c, i) => (
              <div key={c.name} className="flex items-center gap-3 px-4 py-2.5">
                <span className="text-lg">
                  {['🇮🇩','🇻🇳','🇲🇾','🇹🇭','🇵🇭','🇸🇬','🇭🇰','🇦🇪','🇨🇳'][i] || '🌏'}
                </span>
                <span className="flex-1 text-sm text-slate-300">{c.name}</span>
                <span className="text-sm font-mono text-ukmc-400">{c.value}</span>
                <div className="w-16 bg-slate-700 rounded-full h-1">
                  <div
                    className="h-1 rounded-full bg-ukmc-500"
                    style={{ width: `${(c.value / (countryData[0]?.value || 1)) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Dim Sum Funnel */}
        <Card title="Dim Sum / RMB Opportunities">
          <div className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">Feasible (Yes)</span>
              <span className="text-lg font-bold text-emerald-400">{stats?.dim_sum_feasible ?? 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">China-linked</span>
              <span className="text-lg font-bold text-amber-400">{stats?.china_linked ?? 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">Belt & Road</span>
              <span className="text-lg font-bold text-purple-400">{stats?.belt_road ?? 0}</span>
            </div>
            <div className="border-t border-slate-700 pt-3 mt-3">
              <p className="text-xs text-slate-500">Est. Dim Sum issuance pool</p>
              <p className="text-xl font-bold text-amber-300 mt-0.5">
                RMB {((stats?.dim_sum_pool_mn || 0) * 7.2 / 1000).toFixed(1)}B
              </p>
            </div>
          </div>
        </Card>

        {/* Priority breakdown */}
        <Card title="Priority Breakdown">
          <div className="p-4 space-y-4">
            {['HIGH','NORMAL','LOW'].map(p => {
              const count = stats?.by_priority?.[p] ?? 0;
              const total = stats?.active_deals || 1;
              const pct = Math.round((count / total) * 100);
              const colors = {
                HIGH:   { bar: 'bg-red-500',    text: 'text-red-400' },
                NORMAL: { bar: 'bg-blue-500',   text: 'text-blue-400' },
                LOW:    { bar: 'bg-slate-500',  text: 'text-slate-400' },
              };
              return (
                <div key={p}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className={`font-medium ${colors[p].text}`}>{p}</span>
                    <span className="text-slate-400">{count} deals ({pct}%)</span>
                  </div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div className={`h-2 rounded-full ${colors[p].bar}`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      {/* ── Top Deals Table ── */}
      <Card
        title="Top Opportunities (by UKMC Fit Score)"
        action={
          <Link to="/origination/pipeline" className="text-xs text-ukmc-400 hover:text-ukmc-300">
            View Pipeline →
          </Link>
        }
      >
        {topDeals.length === 0 ? (
          <Empty icon="🎯" title="No deals yet" subtitle="Add your first deal to start tracking." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left px-4 py-2 text-xs font-medium text-slate-500 uppercase">Company</th>
                  <th className="text-left px-4 py-2 text-xs font-medium text-slate-500 uppercase hidden sm:table-cell">Type</th>
                  <th className="text-right px-4 py-2 text-xs font-medium text-slate-500 uppercase hidden md:table-cell">Size</th>
                  <th className="text-left px-4 py-2 text-xs font-medium text-slate-500 uppercase">Stage</th>
                  <th className="text-left px-4 py-2 text-xs font-medium text-slate-500 uppercase hidden lg:table-cell">Fit Score</th>
                  <th className="text-left px-4 py-2 text-xs font-medium text-slate-500 uppercase">Urgency</th>
                </tr>
              </thead>
              <tbody>
                {topDeals.map(deal => <DealRow key={deal.id} deal={deal} />)}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* ── Intelligence Signals ── */}
      <Card
        title="Latest Intelligence Signals"
        action={
          <Link to="/origination/intelligence" className="text-xs text-ukmc-400 hover:text-ukmc-300">
            View All →
          </Link>
        }
      >
        {signals.length === 0 ? (
          <div className="p-4">
            <Empty icon="📡" title="No signals yet" subtitle="Run intelligence scan to discover new opportunities." />
          </div>
        ) : (
          <div className="p-4 space-y-3">
            {signals.map(s => <SignalRow key={s.id} signal={s} />)}
          </div>
        )}
      </Card>

    </div>
  );
}
