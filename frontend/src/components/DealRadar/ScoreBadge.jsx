const STYLES = {
  HIGH:   'bg-red-100 text-red-700 border border-red-200',
  MEDIUM: 'bg-yellow-100 text-yellow-700 border border-yellow-200',
  LOW:    'bg-green-100 text-green-700 border border-green-200',
  NOISE:  'bg-gray-100 text-gray-500 border border-gray-200',
};

const EMOJIS = { HIGH: '🔴', MEDIUM: '🟡', LOW: '🟢', NOISE: '⚪' };

export default function ScoreBadge({ score, priority, size = 'md' }) {
  const textSize = size === 'sm' ? 'text-xs' : 'text-sm';
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded font-bold ${textSize} ${STYLES[priority] ?? STYLES.NOISE}`}>
      {EMOJIS[priority]} {score}
    </span>
  );
}
