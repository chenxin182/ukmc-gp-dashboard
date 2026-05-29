import { useEffect, useState, useCallback } from 'react';
import { getContacts, createContact } from '../../api';
import { CountryFlag, Card, Spinner, Empty, fmtDate } from './shared';

const ROLES = ['', 'CEO', 'CFO', 'TREASURY_HEAD', 'PROJECT_DIRECTOR', 'BOARD', 'LEGAL', 'OTHER'];

const ROLE_STYLES = {
  CEO:              'bg-amber-500/20 text-amber-300',
  CFO:              'bg-emerald-500/20 text-emerald-300',
  TREASURY_HEAD:    'bg-blue-500/20 text-blue-300',
  PROJECT_DIRECTOR: 'bg-purple-500/20 text-purple-300',
  BOARD:            'bg-pink-500/20 text-pink-300',
  LEGAL:            'bg-cyan-500/20 text-cyan-300',
};

function RoleBadge({ role }) {
  if (!role) return null;
  const cls = ROLE_STYLES[role] || 'bg-slate-500/20 text-slate-400';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {role.replace('_', ' ')}
    </span>
  );
}

function ContactCard({ c }) {
  const initials = (c.name || '?').split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 hover:border-slate-600 transition-colors">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-full bg-ukmc-800 flex items-center justify-center text-sm font-bold text-ukmc-200 shrink-0">
          {initials}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="font-semibold text-slate-200 text-sm">{c.name}</p>
              <p className="text-xs text-slate-500 mt-0.5">{c.title}</p>
            </div>
            <RoleBadge role={c.role} />
          </div>

          <div className="mt-2 flex items-center gap-1.5">
            {c.country && <CountryFlag country={c.country} />}
            <span className="text-xs text-slate-400">{c.company_name}</span>
            {c.country && <span className="text-slate-700">·</span>}
            {c.country && <span className="text-xs text-slate-500">{c.country}</span>}
          </div>

          <div className="mt-3 space-y-1">
            {c.email && (
              <a href={`mailto:${c.email}`} className="flex items-center gap-1.5 text-xs text-ukmc-400 hover:text-ukmc-300 group">
                <span className="text-slate-600 group-hover:text-slate-400">✉</span>
                {c.email}
              </a>
            )}
            {c.phone && (
              <p className="flex items-center gap-1.5 text-xs text-slate-400">
                <span className="text-slate-600">☎</span>
                {c.phone}
              </p>
            )}
            {c.linkedin && (
              <a href={c.linkedin} target="_blank" rel="noreferrer" className="flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300">
                <span>in</span>
                LinkedIn Profile ↗
              </a>
            )}
          </div>

          {c.notes && (
            <p className="mt-2 text-xs text-slate-500 italic line-clamp-2">{c.notes}</p>
          )}

          <div className="mt-2 flex items-center gap-2">
            {c.is_decision_maker && (
              <span className="text-xs bg-amber-500/10 text-amber-400 px-1.5 py-0.5 rounded">
                Decision Maker
              </span>
            )}
            {c.is_gatekeeper && (
              <span className="text-xs bg-purple-500/10 text-purple-400 px-1.5 py-0.5 rounded">
                Gatekeeper
              </span>
            )}
            {c.priority && (
              <span className="text-xs bg-red-500/10 text-red-400 px-1.5 py-0.5 rounded">
                Priority
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function AddContactModal({ onClose, onSaved }) {
  const [form, setForm] = useState({
    name: '', title: '', role: '', email: '', phone: '', linkedin: '',
    company_name: '', country: '', notes: '',
    is_decision_maker: false, is_gatekeeper: false, priority: false,
  });
  const [saving, setSaving] = useState(false);

  const inp = "w-full bg-slate-900 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-ukmc-500 placeholder-slate-600";
  const upd = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const COUNTRIES = ['Indonesia','Vietnam','Malaysia','Thailand','Philippines','Singapore','Hong Kong','UAE','Saudi Arabia','China'];

  async function save() {
    if (!form.name.trim()) return;
    setSaving(true);
    try {
      await createContact(form);
      onSaved();
      onClose();
    } catch (e) {
      alert('Error: ' + e.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-700">
          <h2 className="font-semibold text-slate-200">Add New Contact</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300">✕</button>
        </div>
        <div className="p-5 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <input className={inp} placeholder="Full Name *" value={form.name} onChange={e => upd('name', e.target.value)} />
            </div>
            <input className={inp} placeholder="Title (e.g. CFO)" value={form.title} onChange={e => upd('title', e.target.value)} />
            <select className={inp} value={form.role} onChange={e => upd('role', e.target.value)}>
              <option value="">Role</option>
              {ROLES.filter(Boolean).map(r => <option key={r}>{r}</option>)}
            </select>
            <input className={inp} placeholder="Company Name" value={form.company_name} onChange={e => upd('company_name', e.target.value)} />
            <select className={inp} value={form.country} onChange={e => upd('country', e.target.value)}>
              <option value="">Country</option>
              {COUNTRIES.map(c => <option key={c}>{c}</option>)}
            </select>
            <input className={inp} placeholder="Email" value={form.email} onChange={e => upd('email', e.target.value)} />
            <input className={inp} placeholder="Phone" value={form.phone} onChange={e => upd('phone', e.target.value)} />
            <div className="col-span-2">
              <input className={inp} placeholder="LinkedIn URL" value={form.linkedin} onChange={e => upd('linkedin', e.target.value)} />
            </div>
            <div className="col-span-2">
              <textarea
                className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-ukmc-500 placeholder-slate-600 resize-none"
                rows={2}
                placeholder="Notes…"
                value={form.notes}
                onChange={e => upd('notes', e.target.value)}
              />
            </div>
          </div>
          <div className="flex flex-wrap gap-4">
            {[
              ['is_decision_maker', 'Decision Maker'],
              ['is_gatekeeper',    'Gatekeeper'],
              ['priority',         'Priority Contact'],
            ].map(([k, l]) => (
              <label key={k} className="flex items-center gap-2 cursor-pointer text-sm text-slate-300">
                <input type="checkbox" className="accent-ukmc-500" checked={form[k]} onChange={e => upd(k, e.target.checked)} />
                {l}
              </label>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-3 px-5 py-4 border-t border-slate-700">
          <button
            onClick={save}
            disabled={saving || !form.name.trim()}
            className="px-5 py-2 bg-ukmc-600 hover:bg-ukmc-500 text-white text-sm rounded-lg transition-colors disabled:opacity-50"
          >
            {saving ? 'Saving…' : 'Save Contact'}
          </button>
          <button onClick={onClose} className="px-4 py-2 text-sm text-slate-400 hover:text-slate-200">
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Contacts() {
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [showAdd, setShowAdd]   = useState(false);
  const [filters, setFilters]   = useState({ q: '', role: '', country: '' });

  const COUNTRIES = ['','Indonesia','Vietnam','Malaysia','Thailand','Philippines','Singapore','Hong Kong','UAE','China'];

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getContacts({ ...filters, limit: 200 });
      setContacts(res.contacts || res);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { load(); }, [load]);

  const byRole = contacts.reduce((acc, c) => {
    const r = c.role || 'OTHER';
    if (!acc[r]) acc[r] = [];
    acc[r].push(c);
    return acc;
  }, {});

  const roleOrder = ['CEO','CFO','TREASURY_HEAD','PROJECT_DIRECTOR','BOARD','LEGAL','OTHER'];

  return (
    <div className="space-y-5 animate-fade-in">

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Contact Intelligence</h1>
          <p className="text-slate-400 text-sm mt-0.5">{contacts.length} contacts across {new Set(contacts.map(c => c.country)).size} countries</p>
        </div>
        <button
          onClick={() => setShowAdd(true)}
          className="px-3 py-1.5 text-sm bg-ukmc-600 hover:bg-ukmc-500 text-white rounded-lg transition-colors"
        >
          + Add Contact
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <input
          className="bg-slate-800 border border-slate-700 text-slate-300 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-ukmc-500 flex-1 min-w-0"
          placeholder="Search name / company…"
          value={filters.q}
          onChange={e => setFilters(f => ({ ...f, q: e.target.value }))}
        />
        <select
          className="bg-slate-800 border border-slate-700 text-slate-300 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-ukmc-500"
          value={filters.role}
          onChange={e => setFilters(f => ({ ...f, role: e.target.value }))}
        >
          {ROLES.map(r => <option key={r} value={r}>{r || 'All Roles'}</option>)}
        </select>
        <select
          className="bg-slate-800 border border-slate-700 text-slate-300 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-ukmc-500"
          value={filters.country}
          onChange={e => setFilters(f => ({ ...f, country: e.target.value }))}
        >
          {COUNTRIES.map(c => <option key={c} value={c}>{c || 'All Countries'}</option>)}
        </select>
      </div>

      {loading ? (
        <div className="flex justify-center py-16"><Spinner /></div>
      ) : contacts.length === 0 ? (
        <Empty icon="👤" title="No contacts found" subtitle="Add contacts to build your relationship intelligence network." />
      ) : (
        <div className="space-y-6">
          {roleOrder.filter(r => byRole[r]?.length > 0).map(role => (
            <div key={role}>
              <div className="flex items-center gap-2 mb-3">
                <RoleBadge role={role} />
                <span className="text-xs text-slate-600">({byRole[role].length})</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                {byRole[role].map(c => <ContactCard key={c.id} c={c} />)}
              </div>
            </div>
          ))}
        </div>
      )}

      {showAdd && (
        <AddContactModal
          onClose={() => setShowAdd(false)}
          onSaved={load}
        />
      )}
    </div>
  );
}
