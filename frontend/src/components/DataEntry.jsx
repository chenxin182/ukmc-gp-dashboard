import { useState } from 'react';
import { calculateEmissions } from '../api';

const ENERGY_OPTIONS = [
  { value: 'sg_electricity', label: 'SG – Grid Electricity',    unit: 'kWh',    factor: '0.4057 kg CO₂e/kWh' },
  { value: 'sg_petrol',      label: 'SG – Petrol / Gasoline',   unit: 'litres', factor: '2.296 kg CO₂e/L'   },
  { value: 'sg_diesel',      label: 'SG – Diesel',              unit: 'litres', factor: '2.68 kg CO₂e/L'    },
  { value: 'my_electricity', label: 'MY – Grid Electricity',    unit: 'kWh',    factor: '0.585 kg CO₂e/kWh' },
  { value: 'my_petrol',      label: 'MY – Petrol / Gasoline',   unit: 'litres', factor: '2.296 kg CO₂e/L'   },
  { value: 'my_diesel',      label: 'MY – Diesel',              unit: 'litres', factor: '2.68 kg CO₂e/L'    },
];

const optionMap = Object.fromEntries(ENERGY_OPTIONS.map(o => [o.value, o]));

let _id = 0;
const newRow = () => ({ id: ++_id, energy_type: 'sg_electricity', consumption: '' });

export default function DataEntry({ onCalculate }) {
  const [companyName, setCompanyName] = useState('');
  const [country, setCountry]         = useState('Singapore');
  const [rows, setRows]               = useState([newRow()]);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState('');

  const addRow    = ()      => setRows(r => [...r, newRow()]);
  const removeRow = (id)    => setRows(r => r.filter(x => x.id !== id));
  const updateRow = (id, k, v) => setRows(r => r.map(x => x.id === id ? { ...x, [k]: v } : x));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!companyName.trim()) {
      setError('Company name is required.');
      return;
    }
    if (rows.some(r => !r.consumption || Number(r.consumption) <= 0)) {
      setError('All consumption values must be positive numbers.');
      return;
    }

    const payload = {
      company_name: companyName.trim(),
      country,
      activities: rows.map(r => ({
        energy_type: r.energy_type,
        consumption: Number(r.consumption),
        unit: optionMap[r.energy_type].unit,
      })),
    };

    setLoading(true);
    try {
      const result = await calculateEmissions(payload);
      onCalculate(result, payload);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-10 px-4">
      <h1 className="text-2xl font-bold text-brand-800 mb-1">Carbon Data Entry</h1>
      <p className="text-gray-500 text-sm mb-8">
        Enter your company's energy consumption to calculate Scope 1 &amp; 2 GHG emissions.
      </p>

      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-xl p-6 space-y-6">

        {/* ── Company info ── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Company Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={companyName}
              onChange={e => setCompanyName(e.target.value)}
              placeholder="e.g. Test Pte Ltd"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
                         focus:ring-2 focus:ring-brand-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reporting Country
            </label>
            <select
              value={country}
              onChange={e => setCountry(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
                         focus:ring-2 focus:ring-brand-500 focus:outline-none"
            >
              <option>Singapore</option>
              <option>Malaysia</option>
            </select>
          </div>
        </div>

        {/* ── Activity rows ── */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-700">
              Energy Consumption Activities
            </h2>
            <button
              type="button"
              onClick={addRow}
              className="text-sm text-brand-700 hover:text-brand-900 font-semibold"
            >
              + Add Row
            </button>
          </div>

          {/* Column headers (desktop) */}
          <div className="hidden sm:grid grid-cols-12 gap-2 text-xs font-medium text-gray-400 px-1 mb-1">
            <div className="col-span-5">Energy Type</div>
            <div className="col-span-3">Consumption</div>
            <div className="col-span-2">Unit</div>
            <div className="col-span-2">Remove</div>
          </div>

          <div className="space-y-2">
            {rows.map(row => (
              <div key={row.id} className="grid grid-cols-12 gap-2 items-center">
                <div className="col-span-12 sm:col-span-5">
                  <select
                    value={row.energy_type}
                    onChange={e => updateRow(row.id, 'energy_type', e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
                               focus:ring-2 focus:ring-brand-500 focus:outline-none"
                  >
                    {ENERGY_OPTIONS.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>

                <div className="col-span-7 sm:col-span-3">
                  <input
                    type="number"
                    min="0"
                    step="any"
                    value={row.consumption}
                    onChange={e => updateRow(row.id, 'consumption', e.target.value)}
                    placeholder="Amount"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
                               focus:ring-2 focus:ring-brand-500 focus:outline-none"
                  />
                </div>

                <div className="col-span-3 sm:col-span-2">
                  <span className="block text-center px-2 py-2 bg-gray-100 text-gray-600
                                   rounded-lg text-sm font-mono">
                    {optionMap[row.energy_type].unit}
                  </span>
                </div>

                <div className="col-span-2 flex justify-center">
                  {rows.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeRow(row.id)}
                      className="text-red-400 hover:text-red-600 text-xl font-bold leading-none"
                      title="Remove row"
                    >
                      ×
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── Emission factors reference ── */}
        <details className="text-xs text-gray-400 cursor-pointer">
          <summary className="font-medium text-gray-500 hover:text-gray-700">
            View emission factors used
          </summary>
          <ul className="mt-2 space-y-0.5 pl-2">
            {ENERGY_OPTIONS.map(o => (
              <li key={o.value}>{o.label}: <span className="font-mono">{o.factor}</span></li>
            ))}
          </ul>
        </details>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-brand-700 hover:bg-brand-800 text-white font-semibold
                     py-3 rounded-lg transition-colors disabled:opacity-60 text-sm"
        >
          {loading ? 'Calculating…' : '⚡ Calculate Emissions'}
        </button>
      </form>

      <div className="mt-4 p-4 bg-brand-50 rounded-lg text-xs text-brand-800 border border-brand-100">
        <span className="font-semibold">Example:</span> SG Electricity 5,000 kWh + MY Diesel 200 L
        → ≈ 2.5635 tCO₂e (Scope 2: 2.0285 + Scope 1: 0.5360)
      </div>
    </div>
  );
}
