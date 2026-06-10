import { useState } from 'react';
import { dr } from '../../api';

const FIELDS = [
  { key: 'name',            label: '公司名称 *', required: true,  placeholder: 'Nexus AI Labs' },
  { key: 'domain',          label: '域名',       required: false, placeholder: 'nexus.ai' },
  { key: 'github_org',      label: 'GitHub Org', required: false, placeholder: 'nexusai' },
  { key: 'twitter_handle',  label: 'Twitter',    required: false, placeholder: 'nexusailabs' },
  { key: 'founder_twitter', label: '创始人 Twitter', required: false, placeholder: 'ceo_handle' },
  { key: 'sector',          label: '领域',       required: false, placeholder: 'AI / Agents' },
  { key: 'stage',           label: '当前阶段',   required: false, placeholder: 'seed' },
  { key: 'greenhouse_token',label: 'Greenhouse Token', required: false, placeholder: 'company-token' },
  { key: 'lever_slug',      label: 'Lever Slug', required: false, placeholder: 'company-name' },
];

export default function AddCompanyModal({ onClose, onAdded }) {
  const [form, setForm] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  function set(key, val) {
    setForm(f => ({ ...f, [key]: val }));
    setError('');
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.name?.trim()) { setError('公司名称不能为空'); return; }
    setLoading(true);
    try {
      await dr.addCompany(form);
      onAdded?.();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-5 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">添加监控公司</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-3">
          {FIELDS.map(({ key, label, required, placeholder }) => (
            <div key={key}>
              <label className="block text-xs font-medium text-gray-700 mb-1">{label}</label>
              <input
                value={form[key] ?? ''}
                onChange={e => set(key, e.target.value)}
                placeholder={placeholder}
                required={required}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
              />
            </div>
          ))}

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose}
              className="flex-1 text-sm border border-gray-200 rounded-lg px-4 py-2 text-gray-600 hover:bg-gray-50">
              取消
            </button>
            <button type="submit" disabled={loading}
              className="flex-1 text-sm bg-brand-700 hover:bg-brand-800 text-white rounded-lg px-4 py-2 disabled:opacity-50 font-medium">
              {loading ? '添加中…' : '添加'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
