import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { downloadReport } from '../api';

const REPORT_SECTIONS = [
  'Executive summary with Scope 1 & 2 breakdown',
  'Emissions by scope — bar chart',
  'Emissions by energy source — pie chart',
  'Activity-level detail table with emission factors',
  'Industry benchmark comparison (SG / MY SME average)',
  'Reduction recommendations',
  'GHG Protocol & ISSB IFRS S2 compliance statement',
];

function ScopeChip({ label, value, bg, text }) {
  return (
    <div className={`rounded-lg p-4 ${bg} text-center`}>
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${text}`}>{Number(value).toFixed(4)}</p>
      <p className="text-xs text-gray-400 mt-0.5">tCO₂e</p>
    </div>
  );
}

export default function ReportPage({ result, formData }) {
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');
  const navigate = useNavigate();

  const handleDownload = async () => {
    setError('');
    setLoading(true);
    try {
      const blob = await downloadReport(formData);
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement('a');
      a.href     = url;
      a.download = `carbon_report_${formData.company_name.replace(/\s+/g, '_')}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-10 px-4">
      <h1 className="text-2xl font-bold text-brand-800 mb-1">PDF Report Generator</h1>
      <p className="text-sm text-gray-500 mb-8">
        GHG Protocol · ISSB IFRS S2 · Singapore NEA &amp; Malaysia GHG Reporting
      </p>

      <div className="bg-white shadow-md rounded-xl p-6 space-y-6">

        {/* Company header */}
        <div className="border-l-4 border-brand-500 pl-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-0.5">Company</p>
          <h2 className="text-xl font-semibold text-gray-800">{result.company_name}</h2>
          <p className="text-sm text-gray-500">{result.country}</p>
        </div>

        {/* Emission summary chips */}
        <div className="grid grid-cols-3 gap-3">
          <ScopeChip label="Total"   value={result.total_emissions}  bg="bg-brand-50"  text="text-brand-800" />
          <ScopeChip label="Scope 1" value={result.scope1_emissions} bg="bg-orange-50" text="text-orange-700" />
          <ScopeChip label="Scope 2" value={result.scope2_emissions} bg="bg-blue-50"   text="text-blue-700" />
        </div>

        {/* What's included */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Report contents:</h3>
          <ul className="space-y-1.5">
            {REPORT_SECTIONS.map(item => (
              <li key={item} className="flex items-start gap-2 text-sm text-gray-600">
                <span className="text-brand-500 mt-0.5 shrink-0">✓</span>
                {item}
              </li>
            ))}
          </ul>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
            {error}
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-3">
          <button
            onClick={handleDownload}
            disabled={loading}
            className="flex-1 bg-brand-700 hover:bg-brand-800 text-white font-semibold
                       py-3 rounded-lg transition-colors disabled:opacity-60
                       flex items-center justify-center gap-2 text-sm"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10"
                          stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Generating PDF…
              </>
            ) : (
              '📄 Download PDF Report'
            )}
          </button>

          <button
            onClick={() => navigate('/dashboard')}
            className="px-5 py-3 border border-gray-300 rounded-lg text-sm text-gray-700
                       hover:bg-gray-50 transition-colors"
          >
            ← Dashboard
          </button>
        </div>
      </div>

      <p className="mt-4 text-xs text-gray-400 text-center">
        PDF generated server-side with ReportLab ·
        Emission factors: EMA Singapore 2025, Suruhanjaya Tenaga Malaysia 2025, IPCC 2006
      </p>
    </div>
  );
}
