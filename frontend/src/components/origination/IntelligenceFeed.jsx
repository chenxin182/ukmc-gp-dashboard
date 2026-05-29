import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSignals, convertSignalToDeal, runIntelligence } from '../../api';
import { UrgencyBadge, CountryFlag, fmtSize, fmtDate, Card, Spinner, Empty } from './shared';

// ─── Signal type config ───────────────────────────────────────────────────────

const SIGNAL_TYPES = {
  EXPANSION:     { icon: '📈', label: 'Expansion',         color: 'text-blue-400' },
  REFINANCING:   { icon: '🔄', label: 'Refinancing',       color: 'text-amber-400' },
  CAPEX:         { icon: '🏗️',  label: 'Capex',             color: 'text-orange-400' },
  ACQUISITION:   { icon: '🤝', label: 'Acquisition',       color: 'text-purple-400' },
  IPO:           { icon: '📊', label: 'IPO / Listing',     color: 'text-green-400' },
  DISTRESS:      { icon: '⚠️',  label: 'Distress',          color: 'text-red-400' },
  SPECTRUM:      { icon: '📡', label: 'Spectrum',          color: 'text-cyan-400' },
  INFRASTRUCTURE:{ icon: '🛤️',  label: 'Infrastructure',    color: 'text-teal-400' },
  SMELTER:       { icon: '⚙️',  label: 'Smelter',           color: 'text-yellow-400' },
  DATA_CENTER:   { icon: '💾', label: 'Data Center',       color: 'text-indigo-400' },
  RENEWABLE:     { icon: '☀️',  label: 'Renewable',         color: 'text-lime-400' },
  BOND_MATURITY: { icon: '📅', label: 'Bond Maturity',     color: 'text-rose-400' },
  M_A:           { icon: '🏦', label: 'M&A',              color: 'text-violet-400' },
};

function SignalCard({ signal, onConvert }) {
  const [converting, setConverting] = useState(false);
  const [done, setDone] = useState(signal.deal_created);
  const navigate = useNavigate();

  const st = SIGNAL_TYPES[signal.signal_type] || { icon: '📰', label: signal.signal_type, color: 'text-slate-400' };

  const urgencyBg = {
    HIGH:   'border-l-red-500',
    MEDIUM: 'border-l-amber-500',
    LOW:    'border-l-slate-600',
  }[signal.urgency] || 'border-l-slate-600';

  async function handleConvert() {
    setConverting(true);
    try {
      const deal = await convertSignalToDeal(signal.id);
      setDone(true);
      onConvert && onConvert(signal.id, deal);
      navigate(`/origination/deals/${deal.id}`);
    } catch (e) {
      alert('Failed: ' + e.message);
    } finally {
      setConverting(false);
    }
  }

  return (
    <div className={`bg-slate-800 border border-slate-700 border-l-2 ${urgencyBg} rounded-xl p-4`}>
      <div className="flex items-start gap-3">
        <span className="text-xl mt-0.5">{st.icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="font-medium text-slate-200 text-sm">{signal.headline}</p>
              <div className="flex items-center gap-2 mt-1 flex-wrap">
                <span className={`text-xs font-medium ${st.color}`}>{st.label}</span>
                <span className="text-slate-600">·</span>
                <CountryFlag country={signal.country} />
                <span className="text-xs text-slate-400">{signal.company_name}</span>
                <span className="text-slate-600">·</span>
                <span className="text-xs text-slate-500">{signal.sector}</span>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <UrgencyBadge urgency={signal.urgency} />
              {signal.financing_implied_mn && (
                <span className="text-xs font-mono text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                  {fmtSize(signal.financing_implied_mn)}
                </span>
              )}
            </div>
          </div>

          {signal.summary && (
            <p className="text-xs text-slate-400 mt-2 leading-relaxed line-clamp-3">{signal.summary}</p>
          )}

          <div className="flex items-center justify-between mt-3">
            <div className="flex items-center gap-3">
              {signal.source_url && (
                <a
                  href={signal.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-ukmc-400 hover:text-ukmc-300"
                  onClick={e => e.stopPropagation()}
                >
                  {signal.source_name || 'Source'} ↗
                </a>
              )}
              <span className="text-xs text-slate-600">{fmtDate(signal.detected_at)}</span>
            </div>

            {done ? (
              <span className="text-xs text-emerald-400 flex items-center gap-1">
                ✓ Deal created
              </span>
            ) : (
              <button
                onClick={handleConvert}
                disabled={converting}
                className="text-xs px-3 py-1 bg-ukmc-600 hover:bg-ukmc-500 text-white rounded-md transition-colors disabled:opacity-50"
              >
                {converting ? 'Converting…' : '→ Create Deal'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Main Intelligence Feed ──────────────────────────────────────────────────

export default function IntelligenceFeed() {
  const [signals, setSignals]   = useState([]);
  const [loading, setLoading]   = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError]       = useState('');
  const [scanResult, setScanResult] = useState(null);
  const [filters, setFilters]   = useState({
    urgency: '', signal_type: '', country: '', reviewed: '', limit: 50,
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await getSignals(filters);
      setSignals(res.signals || res);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { load(); }, [load]);

  async function handleScan() {
    setScanning(true);
    setScanResult(null);
    try {
      const res = await runIntelligence({});
      setScanResult(res);
      load();
    } catch (e) {
      setScanResult({ error: e.message });
    } finally {
      setScanning(false);
    }
  }

  const unreviewed = signals.filter(s => !s.reviewed).length;
  const highUrgency = signals.filter(s => s.urgency === 'HIGH').length;

  return (
    <div className="space-y-5 animate-fade-in">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Intelligence Feed</h1>
          <p className="text-slate-400 text-sm mt-0.5">
            {signals.length} signals · {unreviewed} pending review · {highUrgency} high urgency
          </p>
        </div>
        <button
          onClick={handleScan}
          disabled={scanning}
          className="flex items-center gap-2 px-4 py-2 bg-ukmc-600 hover:bg-ukmc-500 text-white text-sm rounded-lg transition-colors disabled:opacity-50"
        >
          {scanning ? (
            <>
              <span className="inline-block w-3 h-3 border border-white border-t-transparent rounded-full animate-spin" />
              Scanning…
            </>
          ) : (
            <>🔍 Run Intelligence Scan</>
          )}
        </button>
      </div>

      {/* Scan result banner */}
      {scanResult && (
        <div className={`border rounded-xl px-4 py-3 text-sm ${scanResult.error ? 'border-red-500/30 bg-red-500/10 text-red-300' : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'}`}>
          {scanResult.error ? (
            `⚠️ Scan error: ${scanResult.error}`
          ) : (
            `✓ Intelligence scan complete · ${scanResult.new_signals ?? 0} new signals discovered · ${scanResult.high_urgency ?? 0} high urgency`
          )}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        {[
          ['urgency',     ['','HIGH','MEDIUM','LOW'],                     'All Urgency'],
          ['signal_type', ['', ...Object.keys(SIGNAL_TYPES)],            'All Types'],
          ['country',     ['','Indonesia','Vietnam','Malaysia','Thailand','Philippines','Singapore','Hong Kong','UAE','China'], 'All Countries'],
          ['reviewed',    ['','false','true'],                            'Review Status'],
        ].map(([key, opts, label]) => (
          <select
            key={key}
            className="bg-slate-800 border border-slate-700 text-slate-300 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-ukmc-500"
            value={filters[key]}
            onChange={e => setFilters(f => ({ ...f, [key]: e.target.value }))}
          >
            {opts.map(o => (
              <option key={o} value={o}>
                {o === '' ? label : (key === 'reviewed' ? (o === 'true' ? 'Reviewed' : 'Pending') : o)}
              </option>
            ))}
          </select>
        ))}
      </div>

      {/* Signal stat chips */}
      <div className="flex flex-wrap gap-2">
        {Object.entries(
          signals.reduce((acc, s) => {
            const t = s.signal_type;
            acc[t] = (acc[t] || 0) + 1;
            return acc;
          }, {})
        ).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([type, count]) => {
          const st = SIGNAL_TYPES[type] || { icon: '📰', color: 'text-slate-400' };
          return (
            <span key={type} className={`text-xs px-2 py-1 bg-slate-800 border border-slate-700 rounded-full ${st.color}`}>
              {st.icon} {type} <span className="text-slate-400">({count})</span>
            </span>
          );
        })}
      </div>

      {/* Feed */}
      {loading ? (
        <div className="flex justify-center py-16"><Spinner /></div>
      ) : error ? (
        <div className="text-center py-10 text-red-400">{error}</div>
      ) : signals.length === 0 ? (
        <Empty icon="📡" title="No signals found" subtitle="Run an intelligence scan or adjust filters." />
      ) : (
        <div className="space-y-3">
          {signals.map(s => (
            <SignalCard
              key={s.id}
              signal={s}
              onConvert={() => load()}
            />
          ))}
        </div>
      )}
    </div>
  );
}
