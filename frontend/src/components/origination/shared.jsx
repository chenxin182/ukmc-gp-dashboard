/**
 * Shared utility components and helpers for UKMC Deal Origination
 */

// ─── Stage definitions ───────────────────────────────────────────────────────

export const STAGES = [
  { key: 'DISCOVERY', label: 'Discovery',  color: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30' },
  { key: 'RESEARCH',  label: 'Research',   color: 'bg-violet-500/20 text-violet-300 border-violet-500/30' },
  { key: 'ANALYSIS',  label: 'Analysis',   color: 'bg-sky-500/20 text-sky-300 border-sky-500/30' },
  { key: 'OUTREACH',  label: 'Outreach',   color: 'bg-amber-500/20 text-amber-300 border-amber-500/30' },
  { key: 'PROPOSAL',  label: 'Proposal',   color: 'bg-orange-500/20 text-orange-300 border-orange-500/30' },
  { key: 'MANDATE',   label: 'Mandate',    color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' },
  { key: 'CLOSED',    label: 'Closed Won', color: 'bg-green-500/20 text-green-300 border-green-500/30' },
  { key: 'LOST',      label: 'Lost',       color: 'bg-gray-500/20 text-gray-400 border-gray-500/30' },
];

export const STAGE_MAP = Object.fromEntries(STAGES.map(s => [s.key, s]));

export const COUNTRIES = [
  'Indonesia','Vietnam','Malaysia','Thailand','Philippines',
  'Singapore','Hong Kong','UAE','Saudi Arabia','China','India','Cambodia',
];

export const SECTORS = [
  'Telecom','Data Centers','Mining / Nickel','Smelting','Renewable Energy',
  'Power / Energy','Logistics / Ports','Industrial Parks','Infrastructure',
  'Fiber Optic / Subsea Cable','AI Infrastructure','Battery Supply Chain',
  'Oil & Gas','Manufacturing','Fintech','Real Estate','Healthcare',
];

export const FINANCING_TYPES = [
  'Dim Sum Bond','Panda Bond','USD Bond','Project Finance',
  'Bridge Financing','Acquisition Financing','Structured Finance',
  'ECA-backed Financing','Working Capital Loan','Revolving Facility',
  'Trade Finance','Supply Chain Financing','Receivables Financing',
  'ESG / Green Financing','SPAC / PIPE','SBLC/BG Monetization',
  'Prepayment Facility','Infrastructure Financing',
];

export const URGENCY_OPTIONS = ['HIGH','MEDIUM','LOW'];
export const PRIORITY_OPTIONS = ['HIGH','NORMAL','LOW'];

// ─── StageBadge ─────────────────────────────────────────────────────────────

export function StageBadge({ stage }) {
  const s = STAGE_MAP[stage] || { label: stage, color: 'bg-gray-500/20 text-gray-400 border-gray-500/30' };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${s.color}`}>
      {s.label}
    </span>
  );
}

// ─── UrgencyBadge ───────────────────────────────────────────────────────────

export function UrgencyBadge({ urgency }) {
  const map = {
    HIGH:   'bg-red-500/20 text-red-300 border-red-500/30',
    MEDIUM: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    LOW:    'bg-slate-500/20 text-slate-400 border-slate-500/30',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${map[urgency] || map.MEDIUM}`}>
      {urgency}
    </span>
  );
}

// ─── ScoreBar ────────────────────────────────────────────────────────────────

export function ScoreBar({ score, size = 'md' }) {
  const color =
    score >= 75 ? 'bg-emerald-500' :
    score >= 50 ? 'bg-amber-500' :
    score >= 25 ? 'bg-orange-500' : 'bg-red-500';
  const h = size === 'sm' ? 'h-1' : 'h-1.5';
  return (
    <div className="flex items-center gap-2">
      <div className={`flex-1 bg-slate-700 rounded-full ${h} overflow-hidden`}>
        <div
          className={`${h} rounded-full transition-all ${color}`}
          style={{ width: `${Math.min(score, 100)}%` }}
        />
      </div>
      <span className="text-xs font-mono text-slate-300 w-8 text-right">{Math.round(score)}</span>
    </div>
  );
}

// ─── CountryFlag emoji helper ────────────────────────────────────────────────

const FLAGS = {
  Indonesia:    '🇮🇩', Vietnam:     '🇻🇳', Malaysia:   '🇲🇾',
  Thailand:     '🇹🇭', Philippines: '🇵🇭', Singapore:  '🇸🇬',
  'Hong Kong':  '🇭🇰', UAE:         '🇦🇪', China:      '🇨🇳',
  India:        '🇮🇳', 'Saudi Arabia': '🇸🇦', Cambodia: '🇰🇭',
};

export function CountryFlag({ country }) {
  return <span title={country}>{FLAGS[country] || '🌏'}</span>;
}

// ─── StatCard ────────────────────────────────────────────────────────────────

export function StatCard({ label, value, sub, icon, accent = 'text-ukmc-400' }) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-slate-400 uppercase tracking-wider">{label}</p>
          <p className={`text-2xl font-bold mt-1 ${accent}`}>{value}</p>
          {sub && <p className="text-xs text-slate-500 mt-0.5">{sub}</p>}
        </div>
        {icon && <span className="text-2xl opacity-60">{icon}</span>}
      </div>
    </div>
  );
}

// ─── Card wrapper ────────────────────────────────────────────────────────────

export function Card({ children, className = '', title, action }) {
  return (
    <div className={`bg-slate-800 border border-slate-700 rounded-xl ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between px-5 py-3 border-b border-slate-700">
          {title && <h3 className="font-semibold text-slate-200 text-sm">{title}</h3>}
          {action}
        </div>
      )}
      {children}
    </div>
  );
}

// ─── Spinner ─────────────────────────────────────────────────────────────────

export function Spinner({ size = 'md' }) {
  const sz = size === 'sm' ? 'h-4 w-4' : size === 'lg' ? 'h-10 w-10' : 'h-6 w-6';
  return (
    <div className={`${sz} border-2 border-slate-600 border-t-ukmc-400 rounded-full animate-spin`} />
  );
}

// ─── Empty state ─────────────────────────────────────────────────────────────

export function Empty({ icon = '📋', title = 'No data', subtitle = '' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-slate-500">
      <span className="text-4xl mb-3">{icon}</span>
      <p className="font-medium text-slate-400">{title}</p>
      {subtitle && <p className="text-sm mt-1">{subtitle}</p>}
    </div>
  );
}

// ─── formatCurrency ──────────────────────────────────────────────────────────

export function fmtSize(mn) {
  if (!mn) return '—';
  if (mn >= 1000) return `USD ${(mn / 1000).toFixed(1)}B`;
  return `USD ${mn}M`;
}

export function fmtDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
}

// ─── NextActionBadge ─────────────────────────────────────────────────────────

const ACTION_COLORS = {
  'warm intro':          'bg-blue-500/20 text-blue-300',
  'direct outreach':     'bg-purple-500/20 text-purple-300',
  'financing teaser':    'bg-teal-500/20 text-teal-300',
  'mandate proposal':    'bg-amber-500/20 text-amber-300',
  'debt restructuring':  'bg-red-500/20 text-red-300',
  'bond proposal':       'bg-indigo-500/20 text-indigo-300',
  'treasury proposal':   'bg-cyan-500/20 text-cyan-300',
};

export function NextActionBadge({ action }) {
  if (!action) return null;
  const key = Object.keys(ACTION_COLORS).find(k => action.toLowerCase().includes(k));
  const cls = key ? ACTION_COLORS[key] : 'bg-slate-500/20 text-slate-300';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {action}
    </span>
  );
}
