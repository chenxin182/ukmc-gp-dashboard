import { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Cell, PieChart, Pie, Legend,
} from 'recharts';
import { getAnalytics } from '../../api';
import { StatCard, Card, Spinner, Empty, fmtSize, CountryFlag } from './shared';

const COLORS = ['#0c86e8','#f59e0b','#10b981','#8b5cf6','#f97316','#06b6d4','#a3e635','#ec4899','#6366f1','#14b8a6'];

const TT_STYLE = {
  contentStyle: { background: '#1e293b', border: '1px solid #334155', borderRadius: 8 },
  labelStyle:   { color: '#cbd5e1' },
  itemStyle:    { color: '#94a3b8' },
};

export default function Analytics() {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState('');

  useEffect(() => {
    getAnalytics()
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>;
  if (error)   return <div className="text-center py-20 text-red-400">{error}</div>;
  if (!data)   return null;

  const { score_distribution, by_financing_type, weekly_new_deals, top_deals } = data;

  // Prepare pie data for top financing types by size
  const pieSizeData = by_financing_type.slice(0, 7).map(x => ({
    name: x.type.replace(' Financing','').replace(' financing',''),
    value: Math.round(x.size_mn),
  }));

  // Normalize score distribution
  const totalScored = score_distribution.reduce((s, x) => s + x.count, 0);

  return (
    <div className="space-y-6 animate-fade-in">

      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-100">Pipeline Analytics</h1>
        <p className="text-slate-400 text-sm mt-0.5">UKMC origination performance and portfolio composition</p>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Total Scored Deals"
          value={totalScored}
          icon="🎯"
          accent="text-ukmc-400"
        />
        <StatCard
          label="Avg Deal Size"
          value={
            by_financing_type.length
              ? fmtSize(Math.round(by_financing_type.reduce((s,x)=>s+x.size_mn,0) / by_financing_type.reduce((s,x)=>s+x.count,0)))
              : '—'
          }
          icon="💰"
          accent="text-amber-400"
        />
        <StatCard
          label="High-Score Deals (75+)"
          value={score_distribution.find(x => x.range === '76-100')?.count ?? 0}
          sub="strong mandate potential"
          icon="⭐"
          accent="text-emerald-400"
        />
        <StatCard
          label="New This Week"
          value={weekly_new_deals[weekly_new_deals.length - 1]?.count ?? 0}
          icon="📈"
          accent="text-purple-400"
        />
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">

        {/* Score Distribution */}
        <Card title="UKMC Fit Score Distribution">
          <div className="p-4">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={score_distribution}>
                <XAxis dataKey="range" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip {...TT_STYLE} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {score_distribution.map((x, i) => {
                    const color = x.range === '76-100' ? '#10b981' : x.range === '51-75' ? '#f59e0b' : x.range === '26-50' ? '#f97316' : '#ef4444';
                    return <Cell key={i} fill={color} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="grid grid-cols-4 gap-2 mt-3">
              {score_distribution.map((x, i) => {
                const colors = ['text-red-400','text-orange-400','text-amber-400','text-emerald-400'];
                const pct = totalScored > 0 ? Math.round((x.count / totalScored) * 100) : 0;
                return (
                  <div key={x.range} className="text-center">
                    <p className={`text-sm font-bold ${colors[i]}`}>{x.count}</p>
                    <p className="text-xs text-slate-500">{x.range}</p>
                    <p className="text-xs text-slate-600">{pct}%</p>
                  </div>
                );
              })}
            </div>
          </div>
        </Card>

        {/* Weekly trend */}
        <Card title="Weekly Deal Origination Trend">
          <div className="p-4">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={weekly_new_deals}>
                <XAxis dataKey="week" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip {...TT_STYLE} />
                <Bar dataKey="count" fill="#0c86e8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">

        {/* Pipeline by financing type — bar */}
        <Card title="Pipeline Value by Financing Type (USD M)">
          <div className="p-4">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart
                data={by_financing_type.slice(0, 8)}
                layout="vertical"
                margin={{ left: 0, right: 20 }}
              >
                <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis
                  type="category"
                  dataKey="type"
                  tick={{ fill: '#94a3b8', fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                  width={120}
                  tickFormatter={v => v.length > 16 ? v.slice(0, 14) + '…' : v}
                />
                <Tooltip
                  {...TT_STYLE}
                  formatter={v => [`USD ${v}M`, 'Pipeline']}
                />
                <Bar dataKey="size_mn" radius={[0, 4, 4, 0]}>
                  {by_financing_type.slice(0, 8).map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Pie — count by type */}
        <Card title="Deal Count by Financing Type">
          <div className="p-4">
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={by_financing_type.slice(0, 7).map(x => ({ name: x.type.split(' ').slice(0, 2).join(' '), value: x.count }))}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={85}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {by_financing_type.slice(0, 7).map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip {...TT_STYLE} />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-1 mt-2">
              {by_financing_type.slice(0, 5).map((x, i) => (
                <div key={x.type} className="flex items-center gap-2 text-xs">
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ background: COLORS[i] }} />
                  <span className="text-slate-400 truncate flex-1">{x.type}</span>
                  <span className="text-slate-300 font-mono">{x.count}</span>
                  <span className="text-amber-400 font-mono text-xs">{fmtSize(x.size_mn)}</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      {/* Top deals leaderboard */}
      <Card title="Top 5 Deals by UKMC Fit Score">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                {['#','Company','Country','Sector','Financing Type','Size','Fit','Mandate%'].map(h => (
                  <th key={h} className="text-left px-4 py-2.5 text-xs font-medium text-slate-500 uppercase">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {top_deals.map((d, i) => (
                <tr key={i} className="border-b border-slate-700/40 hover:bg-slate-700/20 transition-colors">
                  <td className="px-4 py-3 text-sm font-bold text-slate-500">{i + 1}</td>
                  <td className="px-4 py-3 text-sm font-medium text-slate-200">{d.company_name}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1">
                      <CountryFlag country={d.country} />
                      <span className="text-xs text-slate-400">{d.country}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-400">{d.sector}</td>
                  <td className="px-4 py-3 text-xs text-slate-400">{d.financing_type}</td>
                  <td className="px-4 py-3 text-xs font-mono text-amber-300">{fmtSize(d.estimated_size_mn)}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-slate-700 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="h-1.5 rounded-full bg-ukmc-500"
                          style={{ width: `${d.ukmc_fit_score}%` }}
                        />
                      </div>
                      <span className="text-xs font-mono text-slate-300">{Math.round(d.ukmc_fit_score)}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-xs font-mono text-emerald-400">{Math.round(d.mandate_probability)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

    </div>
  );
}
