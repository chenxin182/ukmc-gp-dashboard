import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getDeal, changeDealStage, updateDeal } from '../../api';
import {
  STAGES, StageBadge, UrgencyBadge, ScoreBar,
  CountryFlag, fmtSize, fmtDate, Card, Spinner, Empty
} from './shared';

// ─── Section block ────────────────────────────────────────────────────────────

function Section({ title, icon, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-5 py-3 text-left border-b border-slate-700 hover:bg-slate-750 transition-colors"
      >
        <div className="flex items-center gap-2">
          {icon && <span>{icon}</span>}
          <span className="font-semibold text-slate-200 text-sm">{title}</span>
        </div>
        <span className="text-slate-500 text-xs">{open ? '▲' : '▼'}</span>
      </button>
      {open && <div className="p-5">{children}</div>}
    </div>
  );
}

// ─── Info row ─────────────────────────────────────────────────────────────────

function InfoRow({ label, value, mono, accent }) {
  if (!value && value !== 0) return null;
  return (
    <div className="flex items-start justify-between gap-4 py-2 border-b border-slate-700/40">
      <span className="text-sm text-slate-500 shrink-0 w-40">{label}</span>
      <span className={`text-sm text-right ${mono ? 'font-mono' : ''} ${accent || 'text-slate-300'}`}>
        {value}
      </span>
    </div>
  );
}

// ─── Stage changer ────────────────────────────────────────────────────────────

function StageChanger({ currentStage, dealId, onChanged }) {
  const [loading, setLoading] = useState(false);

  async function advance() {
    const order = ['DISCOVERY','RESEARCH','ANALYSIS','OUTREACH','PROPOSAL','MANDATE','CLOSED'];
    const idx = order.indexOf(currentStage);
    if (idx < 0 || idx >= order.length - 1) return;
    const next = order[idx + 1];
    setLoading(true);
    try {
      await changeDealStage(dealId, next);
      onChanged(next);
    } catch (e) {
      alert('Error: ' + e.message);
    } finally {
      setLoading(false);
    }
  }

  async function markLost() {
    if (!confirm('Mark this deal as Lost?')) return;
    setLoading(true);
    try {
      await changeDealStage(dealId, 'LOST');
      onChanged('LOST');
    } catch (e) {
      alert('Error: ' + e.message);
    } finally {
      setLoading(false);
    }
  }

  const canAdvance = !['MANDATE','CLOSED','LOST'].includes(currentStage);

  return (
    <div className="flex items-center gap-2">
      {canAdvance && (
        <button
          onClick={advance}
          disabled={loading}
          className="px-3 py-1.5 text-xs bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition-colors disabled:opacity-50"
        >
          {loading ? '…' : '↑ Advance Stage'}
        </button>
      )}
      {!['LOST','CLOSED'].includes(currentStage) && (
        <button
          onClick={markLost}
          disabled={loading}
          className="px-3 py-1.5 text-xs bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-500/30 rounded-lg transition-colors disabled:opacity-50"
        >
          ✕ Mark Lost
        </button>
      )}
    </div>
  );
}

// ─── Contact card ─────────────────────────────────────────────────────────────

function ContactCard({ c }) {
  const roleColors = {
    CEO: 'text-amber-300', CFO: 'text-emerald-300',
    TREASURY_HEAD: 'text-blue-300', PROJECT_DIRECTOR: 'text-purple-300',
    BOARD: 'text-pink-300',
  };
  return (
    <div className="bg-slate-750 border border-slate-700 rounded-lg p-3">
      <div className="flex items-start gap-2">
        <div className="w-8 h-8 rounded-full bg-ukmc-700 flex items-center justify-center text-sm font-bold text-ukmc-200 shrink-0">
          {(c.name || '?')[0]}
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-200">{c.name}</p>
          <p className="text-xs text-slate-400">{c.title}</p>
          {c.role && (
            <p className={`text-xs font-medium mt-0.5 ${roleColors[c.role] || 'text-slate-400'}`}>
              {c.role.replace('_', ' ')}
            </p>
          )}
          <div className="mt-2 space-y-0.5">
            {c.email && (
              <p className="text-xs text-ukmc-400">
                <a href={`mailto:${c.email}`} className="hover:underline">{c.email}</a>
              </p>
            )}
            {c.phone && <p className="text-xs text-slate-500">{c.phone}</p>}
            {c.linkedin && (
              <p className="text-xs">
                <a href={c.linkedin} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">
                  LinkedIn ↗
                </a>
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Activity log ─────────────────────────────────────────────────────────────

function ActivityLog({ activities }) {
  if (!activities?.length) return <p className="text-slate-500 text-sm">No activity recorded.</p>;

  const typeIcon = {
    STAGE_CHANGE: '📊', NOTE: '📝', EMAIL_SENT: '📧',
    MEETING: '🤝', ANALYSIS_RUN: '🔍', CONTACT_ADDED: '👤', SIGNAL_LINKED: '📡',
  };

  return (
    <div className="space-y-2">
      {activities.map(a => (
        <div key={a.id} className="flex items-start gap-2 text-sm">
          <span className="mt-0.5 shrink-0">{typeIcon[a.activity_type] || '•'}</span>
          <div className="min-w-0">
            <p className="text-slate-300 leading-snug">{a.description}</p>
            <p className="text-xs text-slate-600 mt-0.5">{fmtDate(a.created_at)} · {a.user}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Main Deal Detail Page ───────────────────────────────────────────────────

export default function DealDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [deal, setDeal]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState('');
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState({});

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const d = await getDeal(id);
      setDeal(d);
      setEditData(d);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  async function saveEdit() {
    try {
      const updated = await updateDeal(id, editData);
      setDeal(updated);
      setEditing(false);
    } catch (e) {
      alert('Save failed: ' + e.message);
    }
  }

  function handleStageChange(newStage) {
    setDeal(d => ({ ...d, stage: newStage }));
  }

  if (loading) {
    return <div className="flex justify-center py-20"><Spinner size="lg" /></div>;
  }

  if (error || !deal) {
    return (
      <div className="text-center py-20">
        <p className="text-red-400">{error || 'Deal not found'}</p>
        <Link to="/origination/pipeline" className="text-ukmc-400 underline text-sm mt-2 block">← Pipeline</Link>
      </div>
    );
  }

  return (
    <div className="space-y-5 animate-fade-in max-w-5xl">

      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <Link to="/origination" className="hover:text-ukmc-400">Dashboard</Link>
        <span>›</span>
        <Link to="/origination/pipeline" className="hover:text-ukmc-400">Pipeline</Link>
        <span>›</span>
        <span className="text-slate-300">{deal.company_name}</span>
      </div>

      {/* Deal header */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <CountryFlag country={deal.country} />
              <h1 className="text-xl font-bold text-slate-100">{deal.company_name}</h1>
              {deal.priority === 'HIGH' && (
                <span className="bg-red-500/20 text-red-400 text-xs px-2 py-0.5 rounded border border-red-500/30">
                  🔴 HIGH PRIORITY
                </span>
              )}
              {deal.dim_sum_feasible && (
                <span className="bg-amber-500/10 text-amber-400 text-xs px-2 py-0.5 rounded border border-amber-500/30">
                  🏮 DIM SUM
                </span>
              )}
              {deal.belt_road && (
                <span className="bg-red-900/30 text-red-300 text-xs px-2 py-0.5 rounded border border-red-800/30">
                  🇨🇳 BRI
                </span>
              )}
            </div>
            <p className="text-slate-400 mt-1">
              {deal.sector} · {deal.country} · {deal.financing_type}
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {!editing ? (
              <button
                onClick={() => setEditing(true)}
                className="px-3 py-1.5 text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg transition-colors"
              >
                ✏️ Edit
              </button>
            ) : (
              <>
                <button onClick={saveEdit} className="px-3 py-1.5 text-xs bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition-colors">
                  ✓ Save
                </button>
                <button onClick={() => { setEditing(false); setEditData(deal); }} className="px-3 py-1.5 text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg transition-colors">
                  ✕ Cancel
                </button>
              </>
            )}
          </div>
        </div>

        {/* Stage pipeline progress */}
        <div className="mt-5">
          <div className="flex items-center gap-1 overflow-x-auto pb-1">
            {['DISCOVERY','RESEARCH','ANALYSIS','OUTREACH','PROPOSAL','MANDATE','CLOSED'].map((s, i, arr) => {
              const current = arr.indexOf(deal.stage);
              const done = i < current;
              const active = i === current;
              return (
                <div key={s} className="flex items-center gap-1 shrink-0">
                  <div className={`flex flex-col items-center`}>
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-colors
                      ${active ? 'bg-ukmc-600 border-ukmc-400 text-white' :
                        done  ? 'bg-slate-600 border-slate-500 text-slate-300' :
                                'bg-slate-800 border-slate-700 text-slate-600'}`}>
                      {done ? '✓' : i + 1}
                    </div>
                    <span className={`text-xs mt-1 ${active ? 'text-ukmc-300' : done ? 'text-slate-500' : 'text-slate-700'}`}>
                      {s.charAt(0) + s.slice(1).toLowerCase()}
                    </span>
                  </div>
                  {i < arr.length - 1 && (
                    <div className={`h-0.5 w-6 mt-0 ${done ? 'bg-slate-500' : 'bg-slate-800'}`} />
                  )}
                </div>
              );
            })}
            {deal.stage === 'LOST' && (
              <div className="ml-2 bg-red-500/20 text-red-400 text-xs px-2 py-0.5 rounded border border-red-500/30">
                LOST
              </div>
            )}
          </div>
        </div>

        {/* Stage change buttons */}
        <div className="mt-4 flex items-center gap-4">
          <StageChanger currentStage={deal.stage} dealId={deal.id} onChanged={handleStageChange} />
          <div className="text-right">
            <p className="text-xs text-slate-500">UKMC Fit Score</p>
            <div className="w-32 mt-1"><ScoreBar score={deal.ukmc_fit_score} /></div>
          </div>
          <div className="text-right">
            <p className="text-xs text-slate-500">Mandate Probability</p>
            <div className="w-32 mt-1"><ScoreBar score={deal.mandate_probability} /></div>
          </div>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* Left column — main info */}
        <div className="lg:col-span-2 space-y-5">

          {/* Opportunity Summary */}
          <Section title="Opportunity Summary" icon="📋">
            <InfoRow label="Company"          value={deal.company_name} />
            <InfoRow label="Country"          value={deal.country} />
            <InfoRow label="Sector"           value={deal.sector} />
            <InfoRow label="Est. Financing"   value={fmtSize(deal.estimated_size_mn)} mono accent="text-amber-300" />
            <InfoRow label="Currency"         value={deal.currency} />
            <InfoRow label="Purpose"          value={deal.purpose} />
            <InfoRow label="Tenor"            value={deal.tenor} />
            <InfoRow label="Urgency"          value={<UrgencyBadge urgency={deal.urgency} />} />
            <InfoRow label="Source"           value={deal.source} />
            {deal.source_url && (
              <div className="py-2 border-b border-slate-700/40 flex items-center justify-between">
                <span className="text-sm text-slate-500">Source URL</span>
                <a href={deal.source_url} target="_blank" rel="noreferrer" className="text-xs text-ukmc-400 hover:underline">
                  View Source ↗
                </a>
              </div>
            )}
            {deal.company_description && (
              <div className="pt-3">
                <p className="text-xs text-slate-500 mb-1">About the Company</p>
                <p className="text-sm text-slate-300 leading-relaxed">{deal.company_description}</p>
              </div>
            )}
          </Section>

          {/* Financing Angle */}
          <Section title="Financing Angle" icon="💡">
            <InfoRow label="Financing Type" value={deal.financing_type} />
            {deal.why_suitable && (
              <div className="py-2">
                <p className="text-xs text-slate-500 mb-1">Why Suitable</p>
                <p className="text-sm text-slate-300 leading-relaxed">{deal.why_suitable}</p>
              </div>
            )}
            {deal.financing_angle && (
              <div className="py-2 border-t border-slate-700/40">
                <p className="text-xs text-slate-500 mb-1">Financing Angle</p>
                <p className="text-sm text-slate-300 leading-relaxed">{deal.financing_angle}</p>
              </div>
            )}
            {deal.potential_lenders && (
              <div className="py-2 border-t border-slate-700/40">
                <p className="text-xs text-slate-500 mb-1">Potential Lenders / Investors</p>
                <p className="text-sm text-slate-300 leading-relaxed">{deal.potential_lenders}</p>
              </div>
            )}
            {deal.chinese_counterparties && (
              <div className="py-2 border-t border-slate-700/40">
                <p className="text-xs text-slate-500 mb-1">Chinese Counterparties</p>
                <p className="text-sm text-slate-300 leading-relaxed">{deal.chinese_counterparties}</p>
              </div>
            )}
          </Section>

          {/* Dim Sum Bond Feasibility */}
          <Section title="Dim Sum Bond Feasibility" icon="🏮" defaultOpen={deal.dim_sum_feasible}>
            <div className="flex items-center gap-3 mb-4">
              <div className={`text-2xl font-bold ${deal.dim_sum_feasible ? 'text-emerald-400' : 'text-slate-500'}`}>
                {deal.dim_sum_feasible ? '✓ FEASIBLE' : '✗ NOT FEASIBLE'}
              </div>
              {deal.china_linked && (
                <span className="text-xs bg-red-900/30 text-red-300 px-2 py-0.5 rounded border border-red-800/30">
                  🇨🇳 China-linked
                </span>
              )}
              {deal.belt_road && (
                <span className="text-xs bg-red-900/30 text-red-300 px-2 py-0.5 rounded border border-red-800/30">
                  BRI Exposure
                </span>
              )}
            </div>
            {deal.dim_sum_notes && (
              <p className="text-sm text-slate-300 leading-relaxed mb-3">{deal.dim_sum_notes}</p>
            )}
            {deal.dim_sum_size_mn && (
              <InfoRow label="Est. Issuance Size" value={fmtSize(deal.dim_sum_size_mn)} mono accent="text-amber-300" />
            )}
            {deal.dim_sum_tenor && (
              <InfoRow label="Proposed Tenor" value={deal.dim_sum_tenor} />
            )}
            {deal.dim_sum_investor_appeal && (
              <div className="py-2 border-t border-slate-700/40">
                <p className="text-xs text-slate-500 mb-1">Investor Appeal</p>
                <p className="text-sm text-slate-300 leading-relaxed">{deal.dim_sum_investor_appeal}</p>
              </div>
            )}
          </Section>

          {/* Strategic Analysis */}
          <Section title="Strategic Analysis" icon="🧠">
            {deal.entry_strategy && (
              <div className="mb-3">
                <p className="text-xs text-slate-500 mb-1">UKMC Entry Strategy</p>
                <p className="text-sm text-slate-300 leading-relaxed">{deal.entry_strategy}</p>
              </div>
            )}
            {deal.competitive_landscape && (
              <div className="py-2 border-t border-slate-700/40">
                <p className="text-xs text-slate-500 mb-1">Competitive Landscape</p>
                <p className="text-sm text-slate-300 leading-relaxed">{deal.competitive_landscape}</p>
              </div>
            )}
            {deal.objections && (
              <div className="py-2 border-t border-slate-700/40">
                <p className="text-xs text-slate-500 mb-1">Likely Objections</p>
                <p className="text-sm text-slate-300 leading-relaxed">{deal.objections}</p>
              </div>
            )}
            {deal.political_considerations && (
              <div className="py-2 border-t border-slate-700/40">
                <p className="text-xs text-slate-500 mb-1">Political Considerations</p>
                <p className="text-sm text-slate-300 leading-relaxed">{deal.political_considerations}</p>
              </div>
            )}
          </Section>

          {/* Intelligence Source */}
          {deal.intelligence_summary && (
            <Section title="Intelligence Source" icon="📡">
              <p className="text-sm text-slate-300 leading-relaxed">{deal.intelligence_summary}</p>
            </Section>
          )}

          {/* Activity Log */}
          <Section title="Activity Log" icon="📜" defaultOpen={false}>
            <ActivityLog activities={deal.activities} />
          </Section>

        </div>

        {/* Right column — score + contacts */}
        <div className="space-y-5">

          {/* Score card */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
            <h3 className="font-semibold text-slate-200 text-sm mb-4">UKMC Fit Analysis</h3>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs text-slate-400 mb-1">
                  <span>Overall Fit Score</span>
                  <span className="font-mono">{deal.ukmc_fit_score?.toFixed(0)}/100</span>
                </div>
                <ScoreBar score={deal.ukmc_fit_score} />
              </div>
              <div>
                <div className="flex justify-between text-xs text-slate-400 mb-1">
                  <span>Mandate Probability</span>
                  <span className="font-mono">{deal.mandate_probability?.toFixed(0)}%</span>
                </div>
                <ScoreBar score={deal.mandate_probability} />
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-700">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <p className="text-slate-500">Stage</p>
                  <div className="mt-0.5"><StageBadge stage={deal.stage} /></div>
                </div>
                <div>
                  <p className="text-slate-500">Urgency</p>
                  <div className="mt-0.5"><UrgencyBadge urgency={deal.urgency} /></div>
                </div>
                <div>
                  <p className="text-slate-500">Priority</p>
                  <p className={`font-medium mt-0.5 ${deal.priority === 'HIGH' ? 'text-red-400' : deal.priority === 'LOW' ? 'text-slate-500' : 'text-blue-400'}`}>
                    {deal.priority}
                  </p>
                </div>
                <div>
                  <p className="text-slate-500">Created</p>
                  <p className="text-slate-400 mt-0.5">{fmtDate(deal.created_at)}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Recommended Next Action */}
          {deal.next_action && (
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4">
              <h3 className="font-semibold text-amber-300 text-sm mb-2">⚡ Recommended Next Action</h3>
              <p className="text-sm font-medium text-amber-200">{deal.next_action}</p>
              {deal.next_action_detail && (
                <p className="text-xs text-amber-400/80 mt-2 leading-relaxed">{deal.next_action_detail}</p>
              )}
            </div>
          )}

          {/* Key Contacts */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-slate-200 text-sm">Key Contacts</h3>
              <button className="text-xs text-ukmc-400 hover:text-ukmc-300">+ Add</button>
            </div>
            {deal.contacts?.length > 0 ? (
              <div className="space-y-2">
                {deal.contacts.map(c => <ContactCard key={c.id} c={c} />)}
              </div>
            ) : (
              <Empty icon="👤" title="No contacts yet" />
            )}
          </div>

          {/* Quick actions */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
            <h3 className="font-semibold text-slate-200 text-sm mb-3">Quick Actions</h3>
            <div className="space-y-2">
              <button className="w-full text-left px-3 py-2 text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg transition-colors">
                📧 Draft Outreach Email
              </button>
              <button className="w-full text-left px-3 py-2 text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg transition-colors">
                📄 Generate Financing Teaser
              </button>
              <button className="w-full text-left px-3 py-2 text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg transition-colors">
                🔍 Research Competitors
              </button>
              <button className="w-full text-left px-3 py-2 text-xs bg-amber-600/20 hover:bg-amber-600/30 text-amber-400 rounded-lg transition-colors border border-amber-600/20">
                🏮 Dim Sum Bond Analysis
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
