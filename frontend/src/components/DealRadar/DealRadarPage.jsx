import { useCallback, useEffect, useState } from 'react';
import { dr } from '../../api';
import AddCompanyModal from './AddCompanyModal';
import BacktestPanel from './BacktestPanel';
import InferenceCard from './InferenceCard';
import WatchlistPanel from './WatchlistPanel';

const TABS = ['今日情报', '监控列表', '回测报告'];

function StatusBar({ msg, type }) {
  if (!msg) return null;
  const colors = { info: 'bg-blue-50 text-blue-700', error: 'bg-red-50 text-red-700', ok: 'bg-green-50 text-green-700' };
  return (
    <div className={`text-xs px-3 py-1.5 rounded-lg mb-3 ${colors[type] ?? colors.info}`}>
      {msg}
    </div>
  );
}

export default function DealRadarPage() {
  const [tab, setTab]             = useState(0);
  const [inferences, setInferences] = useState([]);
  const [companies, setCompanies]   = useState([]);
  const [minScore, setMinScore]     = useState(40);
  const [days, setDays]             = useState(7);
  const [loading, setLoading]       = useState(true);
  const [runStatus, setRunStatus]   = useState(null);  // {msg, type}
  const [showAdd, setShowAdd]       = useState(false);
  const [agentsRunning, setAgentsRunning] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [infs, cos] = await Promise.all([
        dr.getInferences(days, minScore),
        dr.getCompanies(),
      ]);
      setInferences(infs);
      setCompanies(cos);
    } catch (e) {
      setRunStatus({ msg: `加载失败: ${e.message}`, type: 'error' });
    } finally {
      setLoading(false);
    }
  }, [minScore]);

  useEffect(() => { refresh(); }, [refresh, days]);

  async function runAgents() {
    setAgentsRunning(true);
    setRunStatus({ msg: '正在运行 Signal Agent…', type: 'info' });
    try {
      const s = await dr.runSignals();
      setRunStatus({ msg: `Signal Agent 完成，${s.new_signals} 条新信号。正在推断…`, type: 'info' });
      const i = await dr.runInference();
      setRunStatus({ msg: `完成！${s.new_signals} 条新信号，${i.inferences_created} 条新推断。`, type: 'ok' });
      await refresh();
    } catch (e) {
      setRunStatus({ msg: `运行失败: ${e.message}`, type: 'error' });
    } finally {
      setAgentsRunning(false);
    }
  }

  const highPriority = inferences.filter(i => i.priority === 'HIGH').length;

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            📡 Deal Radar
            {highPriority > 0 && (
              <span className="text-sm bg-red-500 text-white rounded-full px-2 py-0.5 font-semibold">
                {highPriority} 高优
              </span>
            )}
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">Pre-funding signal intelligence</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => { setShowAdd(true); setTab(0); }}
            className="text-sm border border-gray-200 rounded-lg px-3 py-2 text-gray-700 hover:bg-gray-50 transition-colors"
          >
            + 添加公司
          </button>
          <button
            onClick={runAgents}
            disabled={agentsRunning}
            className="text-sm bg-brand-700 hover:bg-brand-800 text-white rounded-lg px-4 py-2 font-medium disabled:opacity-60 transition-colors"
          >
            {agentsRunning ? '运行中…' : '▶ 运行 Agents'}
          </button>
        </div>
      </div>

      <StatusBar {...(runStatus ?? {})} />

      {/* Tabs */}
      <div className="flex gap-1 mb-4 border-b border-gray-200">
        {TABS.map((t, i) => (
          <button
            key={t}
            onClick={() => setTab(i)}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors
              ${tab === i
                ? 'text-brand-700 border-b-2 border-brand-700 -mb-px bg-white'
                : 'text-gray-500 hover:text-gray-700'}`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Tab 0 — Today's inferences */}
      {tab === 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Inferences list */}
          <div className="lg:col-span-2">
            <div className="flex items-center gap-2 mb-3 flex-wrap">
              <span className="text-sm text-gray-500">
                {loading ? '加载中…' : `${inferences.length} 条情报`}
              </span>
              <div className="flex gap-2 ml-auto">
                <select
                  value={days}
                  onChange={e => setDays(Number(e.target.value))}
                  className="text-xs border border-gray-200 rounded px-2 py-1 text-gray-600"
                >
                  <option value={1}>过去24小时</option>
                  <option value={7}>过去7天</option>
                  <option value={30}>过去30天</option>
                </select>
                <select
                  value={minScore}
                  onChange={e => setMinScore(Number(e.target.value))}
                  className="text-xs border border-gray-200 rounded px-2 py-1 text-gray-600"
                >
                  <option value={40}>分数 ≥ 40</option>
                  <option value={60}>分数 ≥ 60</option>
                  <option value={80}>分数 ≥ 80</option>
                </select>
              </div>
            </div>

            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse" />
                ))}
              </div>
            ) : inferences.length === 0 ? (
              <div className="text-center py-16 text-gray-400 bg-white rounded-xl border border-gray-200">
                <div className="text-4xl mb-3">🔍</div>
                <div className="font-medium text-gray-500">今日暂无情报</div>
                <div className="text-sm mt-1">点击「运行 Agents」抓取最新信号</div>
              </div>
            ) : (
              inferences.map(inf => (
                <InferenceCard key={inf.id} inference={inf} onFeedback={refresh} />
              ))
            )}
          </div>

          {/* Watchlist sidebar */}
          <WatchlistPanel
            companies={companies}
            onAdd={() => setShowAdd(true)}
            onRefresh={refresh}
          />
        </div>
      )}

      {/* Tab 1 — Full watchlist management */}
      {tab === 1 && (
        <div className="max-w-lg">
          <WatchlistPanel
            companies={companies}
            onAdd={() => setShowAdd(true)}
            onRefresh={refresh}
          />
        </div>
      )}

      {/* Tab 2 — Backtest */}
      {tab === 2 && <BacktestPanel />}

      {/* Add Company modal */}
      {showAdd && (
        <AddCompanyModal onClose={() => setShowAdd(false)} onAdded={refresh} />
      )}
    </div>
  );
}
