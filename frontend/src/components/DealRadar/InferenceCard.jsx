import { useState } from 'react';
import { dr } from '../../api';
import ScoreBadge from './ScoreBadge';
import SignalChip from './SignalChip';

const EVENT_LABELS = {
  series_a:    'Series A',
  series_b:    'Series B',
  seed:        'Seed',
  acquisition: 'Acquisition',
  pivot:       'Pivot',
  unknown:     'Unknown',
};

export default function InferenceCard({ inference, onFeedback }) {
  const [submitting, setSubmitting] = useState(null);
  const [done, setDone] = useState(null);
  const [expanded, setExpanded] = useState(false);

  async function handleFeedback(outcome) {
    setSubmitting(outcome);
    try {
      await dr.submitFeedback(inference.id, outcome);
      setDone(outcome);
      onFeedback?.();
    } catch (e) {
      console.error(e);
    } finally {
      setSubmitting(null);
    }
  }

  const eventLabel = EVENT_LABELS[inference.event_type] ?? inference.event_type;

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-3 overflow-hidden">
      {/* Header row */}
      <div className="flex items-start justify-between p-4 pb-2">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <ScoreBadge score={inference.confidence_score} priority={inference.priority} />
          <div className="min-w-0">
            <div className="font-semibold text-gray-900 truncate">{inference.company_name}</div>
            <div className="text-xs text-gray-500 mt-0.5">
              预测事件:&nbsp;
              <span className="font-medium text-gray-700">{eventLabel}</span>
              <span className="mx-2 text-gray-300">·</span>
              {new Date(inference.created_at).toLocaleDateString('zh-CN')}
            </div>
          </div>
        </div>

        {/* Feedback / expand */}
        <div className="flex items-center gap-2 ml-3 shrink-0">
          {done ? (
            <span className="text-xs text-gray-400 italic">
              {done === 'confirmed' ? '✓ 已确认' : '✗ 误报'}
            </span>
          ) : (
            <>
              <button
                onClick={() => handleFeedback('confirmed')}
                disabled={!!submitting}
                className="text-xs bg-green-50 hover:bg-green-100 text-green-700 border border-green-200 px-2 py-1 rounded transition-colors disabled:opacity-50"
              >
                {submitting === 'confirmed' ? '…' : '✓ 确认'}
              </button>
              <button
                onClick={() => handleFeedback('false_positive')}
                disabled={!!submitting}
                className="text-xs bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 px-2 py-1 rounded transition-colors disabled:opacity-50"
              >
                {submitting === 'false_positive' ? '…' : '✗ 误报'}
              </button>
            </>
          )}
          <button
            onClick={() => setExpanded(x => !x)}
            className="text-gray-400 hover:text-gray-600 text-xs px-1"
          >
            {expanded ? '▲' : '▼'}
          </button>
        </div>
      </div>

      {/* Reasoning (collapsed by default) */}
      {expanded && (
        <div className="px-4 pb-3 border-t border-gray-50 pt-3">
          <p className="text-sm text-gray-600 leading-relaxed mb-3">{inference.reasoning}</p>
        </div>
      )}

      {/* Signal chips */}
      <div className="px-4 pb-3 flex flex-wrap gap-1.5">
        {(inference.triggered_signals_types ?? []).map((t, i) => (
          <SignalChip key={i} type={t} />
        ))}
        {!inference.triggered_signals_types && inference.triggered_signals?.length > 0 && (
          <span className="text-xs text-gray-400">{inference.triggered_signals.length} signals triggered</span>
        )}
      </div>
    </div>
  );
}
