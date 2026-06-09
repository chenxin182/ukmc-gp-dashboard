const LABELS = {
  hire_finance_ir:     '👔 Finance/IR Hire',
  hire_infra_burst:    '🖥️ Infra Hire Burst',
  github_commit_spike: '⚡ GitHub Spike',
  founder_vc_interact: '🤝 VC Interaction',
  website_update:      '🌐 Website Updated',
  pr_activity_surge:   '🔀 PR Surge',
  team_expansion:      '📈 Team Growth',
  news:                '📰 News Mention',
};

export default function SignalChip({ type }) {
  return (
    <span className="inline-block bg-gray-100 text-gray-700 text-xs px-2 py-0.5 rounded-full border border-gray-200">
      {LABELS[type] ?? type}
    </span>
  );
}
