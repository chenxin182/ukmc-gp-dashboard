import { useState } from 'react';
import { dr } from '../../api';

const STAGE_COLORS = {
  seed:     'bg-purple-50 text-purple-700',
  series_a: 'bg-blue-50 text-blue-700',
  series_b: 'bg-cyan-50 text-cyan-700',
  series_c: 'bg-teal-50 text-teal-700',
  growth:   'bg-orange-50 text-orange-700',
};

function CompanyRow({ company, onSelect, selected, onRemoved }) {
  const [confirming, setConfirming] = useState(false);
  const [removing, setRemoving] = useState(false);

  async function handleRemove() {
    if (!confirming) { setConfirming(true); return; }
    setRemoving(true);
    try {
      await dr.removeCompany(company.id);
      onRemoved?.();
    } catch (e) {
      console.error(e);
    } finally {
      setRemoving(false);
      setConfirming(false);
    }
  }

  const stageClass = STAGE_COLORS[company.stage] ?? 'bg-gray-50 text-gray-600';
  const isSelected = selected === company.id;

  return (
    <div
      onClick={() => onSelect(isSelected ? null : company.id)}
      className={`flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer transition-colors mb-1
        ${isSelected ? 'bg-brand-50 border border-brand-200' : 'hover:bg-gray-50 border border-transparent'}`}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-900 truncate">{company.name}</span>
          {company.stage && (
            <span className={`text-xs px-1.5 py-0.5 rounded font-medium shrink-0 ${stageClass}`}>
              {company.stage.replace('_', ' ')}
            </span>
          )}
        </div>
        {company.sector && (
          <div className="text-xs text-gray-400 mt-0.5 truncate">{company.sector}</div>
        )}
      </div>
      <div className="flex items-center gap-1.5 ml-2 shrink-0">
        {company.github_org && (
          <span className="text-gray-300 text-xs" title="GitHub">⬡</span>
        )}
        <button
          onClick={e => { e.stopPropagation(); handleRemove(); }}
          disabled={removing}
          className={`text-xs px-1.5 py-0.5 rounded transition-colors
            ${confirming
              ? 'bg-red-100 text-red-700 hover:bg-red-200'
              : 'text-gray-300 hover:text-red-400'}`}
        >
          {removing ? '…' : confirming ? '确认?' : '✕'}
        </button>
      </div>
    </div>
  );
}

export default function WatchlistPanel({ companies, onAdd, onSelect, onRefresh }) {
  const [selectedId, setSelectedId] = useState(null);
  const [signals, setSignals] = useState(null);
  const [loadingSignals, setLoadingSignals] = useState(false);

  async function handleSelect(id) {
    setSelectedId(id);
    if (id) {
      setLoadingSignals(true);
      try {
        const data = await dr.getSignals(id, 30);
        setSignals(data);
      } catch (e) {
        setSignals([]);
      } finally {
        setLoadingSignals(false);
      }
    } else {
      setSignals(null);
    }
    onSelect?.(id);
  }

  const selectedCompany = companies.find(c => c.id === selectedId);

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-gray-800 text-sm">
          监控列表
          <span className="ml-2 text-xs font-normal text-gray-400">{companies.length} 家</span>
        </h2>
        <button
          onClick={onAdd}
          className="text-xs bg-brand-700 hover:bg-brand-800 text-white px-2.5 py-1.5 rounded-lg font-medium transition-colors"
        >
          + 添加
        </button>
      </div>

      {/* Company list */}
      {companies.length === 0 ? (
        <div className="text-center py-8 text-gray-400">
          <div className="text-3xl mb-2">🏢</div>
          <div className="text-sm">暂无监控公司</div>
          <button onClick={onAdd} className="text-xs text-brand-600 mt-2 hover:underline">
            添加第一家公司
          </button>
        </div>
      ) : (
        companies.map(c => (
          <CompanyRow
            key={c.id}
            company={c}
            selected={selectedId}
            onSelect={handleSelect}
            onRemoved={onRefresh}
          />
        ))
      )}

      {/* Signal detail for selected company */}
      {selectedId && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="text-xs font-medium text-gray-700 mb-2">
            {selectedCompany?.name} — 近30天信号
          </div>
          {loadingSignals ? (
            <div className="text-xs text-gray-400 py-2">加载中…</div>
          ) : signals?.length === 0 ? (
            <div className="text-xs text-gray-400 py-2">暂无信号记录</div>
          ) : (
            <div className="space-y-1 max-h-48 overflow-y-auto">
              {(signals ?? []).map(s => (
                <div key={s.id} className="flex items-center gap-2 text-xs">
                  <span className="text-gray-400 shrink-0 w-20">
                    {new Date(s.captured_at).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })}
                  </span>
                  <span className="bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded text-xs truncate">
                    {s.signal_type}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
