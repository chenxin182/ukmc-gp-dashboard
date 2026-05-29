import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { createDeal } from '../../api';
import { COUNTRIES, SECTORS, FINANCING_TYPES, URGENCY_OPTIONS, PRIORITY_OPTIONS } from './shared';

function Field({ label, required, children, hint }) {
  return (
    <div>
      <label className="block text-xs font-medium text-slate-400 mb-1">
        {label} {required && <span className="text-red-400">*</span>}
      </label>
      {children}
      {hint && <p className="text-xs text-slate-600 mt-0.5">{hint}</p>}
    </div>
  );
}

const input = "w-full bg-slate-900 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-ukmc-500 placeholder-slate-600";
const textarea = "w-full bg-slate-900 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-ukmc-500 placeholder-slate-600 resize-none";
const select = "w-full bg-slate-900 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-ukmc-500";

function Section({ title, icon, children }) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
      <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
        <span>{icon}</span>{title}
      </h3>
      <div className="space-y-4">{children}</div>
    </div>
  );
}

// Inline contact row
function ContactRow({ contact, idx, onChange, onRemove }) {
  const roles = ['CEO','CFO','TREASURY_HEAD','PROJECT_DIRECTOR','BOARD','LEGAL','OTHER'];
  const upd = (k, v) => onChange(idx, { ...contact, [k]: v });
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-lg p-3 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs text-slate-500">Contact #{idx + 1}</span>
        <button onClick={() => onRemove(idx)} className="text-xs text-red-400 hover:text-red-300">✕ Remove</button>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <input className={input} placeholder="Full Name *" value={contact.name} onChange={e => upd('name', e.target.value)} />
        <input className={input} placeholder="Title (e.g. CFO)" value={contact.title} onChange={e => upd('title', e.target.value)} />
        <select className={select} value={contact.role} onChange={e => upd('role', e.target.value)}>
          <option value="">Role</option>
          {roles.map(r => <option key={r}>{r}</option>)}
        </select>
        <input className={input} placeholder="Email" value={contact.email} onChange={e => upd('email', e.target.value)} />
        <input className={input} placeholder="Phone" value={contact.phone} onChange={e => upd('phone', e.target.value)} />
        <input className={input} placeholder="LinkedIn URL" value={contact.linkedin} onChange={e => upd('linkedin', e.target.value)} />
      </div>
    </div>
  );
}

export default function NewDeal() {
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [error, setError]   = useState('');

  const [form, setForm] = useState({
    // Core
    company_name: '',
    country: '',
    sector: '',
    company_description: '',
    // Financing
    financing_type: '',
    estimated_size_mn: '',
    currency: 'USD',
    purpose: '',
    tenor: '',
    urgency: 'MEDIUM',
    priority: 'NORMAL',
    stage: 'DISCOVERY',
    // Flags
    china_linked: false,
    belt_road: false,
    dim_sum_feasible: false,
    // Analysis
    why_suitable: '',
    financing_angle: '',
    potential_lenders: '',
    chinese_counterparties: '',
    // Dim Sum
    dim_sum_notes: '',
    dim_sum_size_mn: '',
    dim_sum_tenor: '',
    dim_sum_investor_appeal: '',
    // Strategy
    entry_strategy: '',
    competitive_landscape: '',
    objections: '',
    political_considerations: '',
    next_action: '',
    next_action_detail: '',
    // Source
    source: 'manual',
    source_url: '',
    intelligence_summary: '',
  });

  const [contacts, setContacts] = useState([]);

  const upd = (k, v) => setForm(f => ({ ...f, [k]: v }));
  const check = (k) => (e) => upd(k, e.target.checked);

  function addContact() {
    setContacts(c => [...c, { name: '', title: '', role: '', email: '', phone: '', linkedin: '' }]);
  }
  function updateContact(idx, val) {
    setContacts(c => c.map((x, i) => i === idx ? val : x));
  }
  function removeContact(idx) {
    setContacts(c => c.filter((_, i) => i !== idx));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.company_name.trim()) { setError('Company name is required'); return; }
    setSaving(true);
    setError('');
    try {
      const payload = {
        ...form,
        estimated_size_mn: form.estimated_size_mn ? parseFloat(form.estimated_size_mn) : null,
        dim_sum_size_mn: form.dim_sum_size_mn ? parseFloat(form.dim_sum_size_mn) : null,
        contacts: contacts.filter(c => c.name.trim()),
      };
      const deal = await createDeal(payload);
      navigate(`/origination/deals/${deal.id}`);
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  const NEXT_ACTIONS = [
    'Warm intro via intermediary','Direct outreach — email','Financing teaser delivery',
    'Mandate proposal submission','Debt restructuring discussion','Dim Sum bond proposal',
    'Treasury optimization proposal','ECA financing angle','Research & monitor',
  ];

  const SOURCES = ['manual','intelligence','referral','conference','network','linkedin'];

  return (
    <div className="max-w-3xl space-y-5 animate-fade-in">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">New Deal Opportunity</h1>
          <p className="text-slate-400 text-sm mt-0.5">Add a new deal to the UKMC origination pipeline</p>
        </div>
        <Link to="/origination/pipeline" className="text-sm text-slate-400 hover:text-slate-200">
          ← Pipeline
        </Link>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-300 rounded-xl px-4 py-3 text-sm">
          ⚠️ {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">

        {/* Company & Geography */}
        <Section title="Company & Geography" icon="🏢">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <Field label="Company Name" required>
                <input
                  className={input}
                  placeholder="e.g. PT Indosat Ooredoo Hutchison"
                  value={form.company_name}
                  onChange={e => upd('company_name', e.target.value)}
                />
              </Field>
            </div>
            <Field label="Country">
              <select className={select} value={form.country} onChange={e => upd('country', e.target.value)}>
                <option value="">Select country</option>
                {COUNTRIES.map(c => <option key={c}>{c}</option>)}
              </select>
            </Field>
            <Field label="Sector">
              <select className={select} value={form.sector} onChange={e => upd('sector', e.target.value)}>
                <option value="">Select sector</option>
                {SECTORS.map(s => <option key={s}>{s}</option>)}
              </select>
            </Field>
            <div className="col-span-2">
              <Field label="Company Description" hint="Brief background on the company">
                <textarea className={textarea} rows={3} placeholder="Describe the company, its operations, and relevance to UKMC…" value={form.company_description} onChange={e => upd('company_description', e.target.value)} />
              </Field>
            </div>
          </div>
        </Section>

        {/* Financing Details */}
        <Section title="Financing Details" icon="💰">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <Field label="Financing Type">
                <select className={select} value={form.financing_type} onChange={e => upd('financing_type', e.target.value)}>
                  <option value="">Select type</option>
                  {FINANCING_TYPES.map(f => <option key={f}>{f}</option>)}
                </select>
              </Field>
            </div>
            <Field label="Est. Deal Size (USD M)" hint="Approximate deal size in USD millions">
              <input
                className={input}
                type="number"
                min="0"
                placeholder="e.g. 250"
                value={form.estimated_size_mn}
                onChange={e => upd('estimated_size_mn', e.target.value)}
              />
            </Field>
            <Field label="Tenor">
              <input className={input} placeholder="e.g. 5 years" value={form.tenor} onChange={e => upd('tenor', e.target.value)} />
            </Field>
            <div className="col-span-2">
              <Field label="Financing Purpose">
                <input className={input} placeholder="e.g. Capex for 5G network expansion, refinancing of maturing USD bonds" value={form.purpose} onChange={e => upd('purpose', e.target.value)} />
              </Field>
            </div>
            <Field label="Urgency">
              <select className={select} value={form.urgency} onChange={e => upd('urgency', e.target.value)}>
                {URGENCY_OPTIONS.map(u => <option key={u}>{u}</option>)}
              </select>
            </Field>
            <Field label="Priority">
              <select className={select} value={form.priority} onChange={e => upd('priority', e.target.value)}>
                {PRIORITY_OPTIONS.map(p => <option key={p}>{p}</option>)}
              </select>
            </Field>
            <Field label="Initial Stage">
              <select className={select} value={form.stage} onChange={e => upd('stage', e.target.value)}>
                {['DISCOVERY','RESEARCH','ANALYSIS','OUTREACH','PROPOSAL'].map(s => <option key={s}>{s}</option>)}
              </select>
            </Field>
            <Field label="Source">
              <select className={select} value={form.source} onChange={e => upd('source', e.target.value)}>
                {SOURCES.map(s => <option key={s}>{s}</option>)}
              </select>
            </Field>
            <div className="col-span-2">
              <Field label="Source URL">
                <input className={input} placeholder="https://…" value={form.source_url} onChange={e => upd('source_url', e.target.value)} />
              </Field>
            </div>
          </div>

          {/* Flags */}
          <div className="flex flex-wrap gap-4 pt-2">
            {[
              ['china_linked', '🇨🇳 China-linked Revenue/Operations'],
              ['belt_road',    '🛤️  Belt & Road Exposure'],
              ['dim_sum_feasible', '🏮 Dim Sum Bond Feasible'],
            ].map(([key, label]) => (
              <label key={key} className="flex items-center gap-2 cursor-pointer group">
                <input
                  type="checkbox"
                  className="w-4 h-4 accent-ukmc-500"
                  checked={form[key]}
                  onChange={check(key)}
                />
                <span className="text-sm text-slate-300 group-hover:text-slate-100">{label}</span>
              </label>
            ))}
          </div>
        </Section>

        {/* Analysis */}
        <Section title="Financing Analysis" icon="💡">
          <Field label="Why Suitable for UKMC">
            <textarea className={textarea} rows={3} placeholder="Why is this deal well-suited for UKMC? What is the unique angle?" value={form.why_suitable} onChange={e => upd('why_suitable', e.target.value)} />
          </Field>
          <Field label="Financing Angle">
            <textarea className={textarea} rows={3} placeholder="Describe the recommended financing structure and rationale…" value={form.financing_angle} onChange={e => upd('financing_angle', e.target.value)} />
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Potential Lenders / Investors">
              <textarea className={textarea} rows={2} placeholder="CITIC Securities, CICC, OCBC, DBS…" value={form.potential_lenders} onChange={e => upd('potential_lenders', e.target.value)} />
            </Field>
            <Field label="Chinese Counterparties">
              <textarea className={textarea} rows={2} placeholder="EPC, shareholders, off-takers, lenders…" value={form.chinese_counterparties} onChange={e => upd('chinese_counterparties', e.target.value)} />
            </Field>
          </div>
        </Section>

        {/* Dim Sum Details (show when relevant) */}
        {(form.dim_sum_feasible || form.china_linked) && (
          <Section title="Dim Sum Bond Details" icon="🏮">
            <div className="grid grid-cols-2 gap-4">
              <Field label="Est. Issuance Size (USD M)">
                <input className={input} type="number" placeholder="e.g. 200" value={form.dim_sum_size_mn} onChange={e => upd('dim_sum_size_mn', e.target.value)} />
              </Field>
              <Field label="Proposed Tenor">
                <input className={input} placeholder="e.g. 3Y, 5Y, 5-7Y" value={form.dim_sum_tenor} onChange={e => upd('dim_sum_tenor', e.target.value)} />
              </Field>
            </div>
            <Field label="Feasibility Notes">
              <textarea className={textarea} rows={3} placeholder="Why is Dim Sum issuance feasible? Chinese revenue, BRI exposure, HK listing, RMB settlement…" value={form.dim_sum_notes} onChange={e => upd('dim_sum_notes', e.target.value)} />
            </Field>
            <Field label="Investor Appeal">
              <textarea className={textarea} rows={2} placeholder="Which Chinese institutional investors would be interested? Why?" value={form.dim_sum_investor_appeal} onChange={e => upd('dim_sum_investor_appeal', e.target.value)} />
            </Field>
          </Section>
        )}

        {/* Strategy */}
        <Section title="Strategic Analysis" icon="🧠">
          <Field label="UKMC Entry Strategy">
            <textarea className={textarea} rows={3} placeholder="How should UKMC approach this opportunity? Warm intro, direct outreach, teaser…" value={form.entry_strategy} onChange={e => upd('entry_strategy', e.target.value)} />
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Competitive Landscape">
              <textarea className={textarea} rows={2} placeholder="Who else is competing for this mandate?" value={form.competitive_landscape} onChange={e => upd('competitive_landscape', e.target.value)} />
            </Field>
            <Field label="Likely Objections">
              <textarea className={textarea} rows={2} placeholder="What pushback should UKMC anticipate?" value={form.objections} onChange={e => upd('objections', e.target.value)} />
            </Field>
            <div className="col-span-2">
              <Field label="Political / Regulatory Considerations">
                <textarea className={textarea} rows={2} placeholder="Any political sensitivities, regulatory approvals, or government relationships involved?" value={form.political_considerations} onChange={e => upd('political_considerations', e.target.value)} />
              </Field>
            </div>
          </div>
        </Section>

        {/* Next Action */}
        <Section title="Recommended Next Action" icon="⚡">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Next Action">
              <select className={select} value={form.next_action} onChange={e => upd('next_action', e.target.value)}>
                <option value="">Select action</option>
                {NEXT_ACTIONS.map(a => <option key={a}>{a}</option>)}
              </select>
            </Field>
          </div>
          <Field label="Action Detail">
            <textarea className={textarea} rows={2} placeholder="Specific steps, timeline, or notes for the recommended action…" value={form.next_action_detail} onChange={e => upd('next_action_detail', e.target.value)} />
          </Field>
        </Section>

        {/* Intelligence Notes */}
        <Section title="Intelligence Notes" icon="📡">
          <Field label="Source / Intelligence Summary">
            <textarea className={textarea} rows={3} placeholder="How was this opportunity discovered? What signals triggered this entry?" value={form.intelligence_summary} onChange={e => upd('intelligence_summary', e.target.value)} />
          </Field>
        </Section>

        {/* Contacts */}
        <Section title="Key Contacts" icon="👤">
          {contacts.length > 0 && (
            <div className="space-y-3">
              {contacts.map((c, i) => (
                <ContactRow key={i} contact={c} idx={i} onChange={updateContact} onRemove={removeContact} />
              ))}
            </div>
          )}
          <button
            type="button"
            onClick={addContact}
            className="text-sm text-ukmc-400 hover:text-ukmc-300 flex items-center gap-1"
          >
            + Add Contact
          </button>
        </Section>

        {/* Submit */}
        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 bg-ukmc-600 hover:bg-ukmc-500 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {saving && <span className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin" />}
            {saving ? 'Creating Deal…' : '✓ Create Deal'}
          </button>
          <Link to="/origination/pipeline" className="px-6 py-2.5 text-sm text-slate-400 hover:text-slate-200">
            Cancel
          </Link>
          <p className="text-xs text-slate-500 ml-auto">
            UKMC Fit Score will be auto-calculated on save
          </p>
        </div>

      </form>
    </div>
  );
}
