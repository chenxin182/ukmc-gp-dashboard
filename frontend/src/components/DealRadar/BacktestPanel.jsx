import { useEffect, useState } from 'react';
import { dr } from '../../api';
import ScoreBadge from './ScoreBadge';

export default function BacktestPanel() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    dr.getBacktest()
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-sm text-gray-400 py-4 text-center">加载回测数据…</div>;
  if (error)   return <div className="text-sm text-red-500 py-4 text-center">{error}</div>;
  if (!data)   return null;

  const pct = Math.round((data.detected / data.total) * 100);

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      {/* Summary */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-gray-800 text-sm">回测报告</h2>
        <div className="text-right">
          <div className="text-2xl font-bold text-gray-900">{pct}%</div>
          <div className="text-xs text-gray-500">Recall ({data.detected}/{data.total})</div>
        </div>
      </div>

      {/* Weight suggestions */}
      {data.weight_suggestions?.weight_suggestions &&
        Object.keys(data.weight_suggestions.weight_suggestions).length > 0 && (
        <div className="mb-4 p-3 bg-yellow-50 rounded-lg border border-yellow-100">
          <div className="text-xs font-medium text-yellow-800 mb-2">权重校准建议</div>
          {Object.entries(data.weight_suggestions.weight_suggestions).map(([sig, info]) => (
            <div key={sig} className="flex justify-between text-xs text-yellow-700 py-0.5">
              <span className="font-mono">{sig}</span>
              <span>{info.current_weight} → <b>{info.suggested_weight}</b> (漏检{info.missed_cases}次)</span>
            </div>
          ))}
        </div>
      )}

      {/* Results table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-gray-400 border-b border-gray-100">
              <th className="text-left py-1.5 font-medium">公司</th>
              <th className="text-left py-1.5 font-medium">轮次</th>
              <th className="text-right py-1.5 font-medium">分数</th>
              <th className="text-right py-1.5 font-medium">检出</th>
            </tr>
          </thead>
          <tbody>
            {(data.results ?? []).map((r, i) => (
              <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                <td className="py-1.5 text-gray-800 font-medium max-w-[120px] truncate">{r.company}</td>
                <td className="py-1.5 text-gray-500">{r.round_type}</td>
                <td className="py-1.5 text-right">
                  <ScoreBadge score={r.score} priority={r.band} size="sm" />
                </td>
                <td className="py-1.5 text-right">
                  {r.detected ? (
                    <span className="text-green-600 font-bold">✓</span>
                  ) : (
                    <span className="text-red-400">✗</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
