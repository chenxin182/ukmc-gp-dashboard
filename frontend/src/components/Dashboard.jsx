import { useNavigate } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer,
  PieChart, Pie, Legend,
} from 'recharts';

const COLORS = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336', '#00BCD4'];

const fmt4 = v => Number(v).toFixed(4);

function StatCard({ title, value, unit, accent }) {
  const color = accent === 'green'  ? 'text-brand-800'
              : accent === 'orange' ? 'text-orange-600'
              :                       'text-blue-700';
  return (
    <div className="bg-white shadow rounded-xl p-5">
      <p className="text-xs text-gray-500 mb-1 uppercase tracking-wide">{title}</p>
      <p className={`text-3xl font-bold ${color}`}>{fmt4(value)}</p>
      <p className="text-xs text-gray-400 mt-1">{unit}</p>
    </div>
  );
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-200 shadow rounded px-3 py-2 text-xs">
      <p className="font-medium">{payload[0].payload.name}</p>
      <p className="text-brand-800">{fmt4(payload[0].value)} tCO₂e</p>
    </div>
  );
}

export default function Dashboard({ result }) {
  const navigate = useNavigate();

  const barData = result.details.map((d, i) => ({
    name: d.name
      .replace('Singapore', 'SG').replace('Malaysia', 'MY')
      .replace('Petrol / Gasoline', 'Petrol')
      .replace('Grid Electricity', 'Electricity'),
    emissions: d.emissions,
    color: COLORS[i % COLORS.length],
  }));

  const pieData = result.details
    .filter(d => d.emissions > 0)
    .map((d, i) => ({
      name: d.name.replace('Singapore', 'SG').replace('Malaysia', 'MY'),
      value: d.emissions,
      color: COLORS[i % COLORS.length],
    }));

  return (
    <div className="max-w-5xl mx-auto py-10 px-4">

      {/* ── Header ── */}
      <div className="flex flex-wrap items-start justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-brand-800">{result.company_name}</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {result.country} · GHG Protocol Scope 1 &amp; 2
          </p>
        </div>
        <button
          onClick={() => navigate('/report')}
          className="bg-brand-700 hover:bg-brand-800 text-white px-5 py-2.5 rounded-lg
                     text-sm font-medium transition-colors shadow"
        >
          Generate PDF Report →
        </button>
      </div>

      {/* ── Stat cards ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <StatCard title="Total GHG Emissions" value={result.total_emissions}  unit="tCO₂e" accent="green"  />
        <StatCard title="Scope 1 — Direct"    value={result.scope1_emissions} unit="tCO₂e" accent="orange" />
        <StatCard title="Scope 2 — Electricity" value={result.scope2_emissions} unit="tCO₂e" accent="blue" />
      </div>

      {/* ── Charts row ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">

        {/* Bar chart */}
        <div className="bg-white shadow rounded-xl p-5">
          <h2 className="text-sm font-semibold text-gray-600 mb-4">
            Emissions by Energy Source (tCO₂e)
          </h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={barData} margin={{ top: 5, right: 10, left: 5, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 10 }}
                angle={-30}
                textAnchor="end"
                interval={0}
              />
              <YAxis
                tick={{ fontSize: 10 }}
                tickFormatter={v => v.toFixed(3)}
                width={55}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="emissions" radius={[4, 4, 0, 0]}>
                {barData.map((d, i) => (
                  <Cell key={i} fill={d.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pie chart */}
        <div className="bg-white shadow rounded-xl p-5">
          <h2 className="text-sm font-semibold text-gray-600 mb-4">
            Emissions Share by Source
          </h2>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="45%"
                outerRadius={75}
                dataKey="value"
                label={({ percent }) => `${(percent * 100).toFixed(1)}%`}
                labelLine
              >
                {pieData.map((d, i) => (
                  <Cell key={i} fill={d.color} />
                ))}
              </Pie>
              <Tooltip formatter={v => [`${fmt4(v)} tCO₂e`]} />
              <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Detail table ── */}
      <div className="bg-white shadow rounded-xl p-5">
        <h2 className="text-sm font-semibold text-gray-600 mb-4">Activity Details</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-brand-50 text-gray-600">
                <th className="text-left py-2 px-3 font-medium">Energy Type</th>
                <th className="text-right py-2 px-3 font-medium">Consumption</th>
                <th className="text-center py-2 px-3 font-medium">Unit</th>
                <th className="text-right py-2 px-3 font-medium">Factor (tCO₂e/unit)</th>
                <th className="text-right py-2 px-3 font-medium">Emissions (tCO₂e)</th>
                <th className="text-center py-2 px-3 font-medium">Scope</th>
              </tr>
            </thead>
            <tbody>
              {result.details.map((d, i) => (
                <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="py-2 px-3 text-gray-800">{d.name}</td>
                  <td className="py-2 px-3 text-right">{Number(d.consumption).toLocaleString()}</td>
                  <td className="py-2 px-3 text-center text-gray-500 font-mono text-xs">{d.unit}</td>
                  <td className="py-2 px-3 text-right text-gray-500 font-mono text-xs">
                    {d.emission_factor.toFixed(7)}
                  </td>
                  <td className="py-2 px-3 text-right font-semibold text-brand-800">
                    {d.emissions.toFixed(4)}
                  </td>
                  <td className="py-2 px-3 text-center">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      d.scope === 1
                        ? 'bg-orange-100 text-orange-700'
                        : 'bg-blue-100 text-blue-700'
                    }`}>
                      Scope {d.scope}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t-2 border-brand-200 bg-brand-50 font-semibold">
                <td colSpan={4} className="py-2 px-3 text-brand-800">Total</td>
                <td className="py-2 px-3 text-right text-brand-800 font-bold">
                  {result.total_emissions.toFixed(4)}
                </td>
                <td />
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      <p className="mt-5 text-xs text-gray-400 text-center">
        GHG Protocol Corporate Standard · ISSB IFRS S2 ·
        EMA Singapore 2025 · Suruhanjaya Tenaga Malaysia 2025 · IPCC 2006
      </p>
    </div>
  );
}
