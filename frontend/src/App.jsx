import { useState } from 'react';
import { BrowserRouter, NavLink, Route, Routes, useNavigate, Link, useLocation } from 'react-router-dom';

// ESG module
import Dashboard  from './components/Dashboard';
import DataEntry  from './components/DataEntry';
import ReportPage from './components/ReportPage';

// Origination module
import DealDashboard    from './components/origination/DealDashboard';
import Pipeline         from './components/origination/Pipeline';
import DealDetail       from './components/origination/DealDetail';
import IntelligenceFeed from './components/origination/IntelligenceFeed';
import NewDeal          from './components/origination/NewDeal';
import Contacts         from './components/origination/Contacts';
import Analytics        from './components/origination/Analytics';

// ─── Origination Nav ─────────────────────────────────────────────────────────

const ORIG_NAV = [
  { to: '/origination',             label: 'Dashboard',    end: true,  icon: '⬡' },
  { to: '/origination/pipeline',    label: 'Pipeline',     end: false, icon: '◈' },
  { to: '/origination/intelligence',label: 'Intelligence', end: false, icon: '◉' },
  { to: '/origination/contacts',    label: 'Contacts',     end: false, icon: '◎' },
  { to: '/origination/analytics',   label: 'Analytics',   end: false, icon: '◆' },
];

function OriginationLayout({ children }) {
  const loc = useLocation();

  const navCls = ({ isActive }) =>
    `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-ukmc-700 text-white'
        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
    }`;

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Top bar */}
      <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-40">
        <div className="max-w-screen-xl mx-auto px-4 py-0">
          <div className="flex items-center justify-between h-14">
            {/* Brand */}
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-ukmc-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">U</span>
              </div>
              <div className="hidden sm:block">
                <p className="text-sm font-bold text-slate-100 leading-none">UKMC International</p>
                <p className="text-xs text-slate-500 leading-none mt-0.5">Deal Origination Platform</p>
              </div>
            </div>

            {/* Module toggle */}
            <div className="flex items-center gap-1 bg-slate-800 border border-slate-700 rounded-lg p-0.5">
              <Link
                to="/origination"
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  loc.pathname.startsWith('/origination')
                    ? 'bg-ukmc-700 text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Origination
              </Link>
              <Link
                to="/"
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  !loc.pathname.startsWith('/origination')
                    ? 'bg-brand-800 text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                ESG Carbon
              </Link>
            </div>

            {/* Right actions */}
            <div className="flex items-center gap-2">
              <Link
                to="/origination/new-deal"
                className="hidden sm:flex items-center gap-1 px-3 py-1.5 bg-ukmc-600 hover:bg-ukmc-500 text-white text-xs font-medium rounded-lg transition-colors"
              >
                + New Deal
              </Link>
              <div className="w-7 h-7 rounded-full bg-ukmc-700 flex items-center justify-center text-xs font-bold text-ukmc-200">
                U
              </div>
            </div>
          </div>
        </div>

        {/* Sub navigation */}
        {loc.pathname.startsWith('/origination') && (
          <div className="border-t border-slate-800">
            <div className="max-w-screen-xl mx-auto px-4">
              <nav className="flex items-center gap-1 overflow-x-auto py-1 scrollbar-none">
                {ORIG_NAV.map(n => (
                  <NavLink key={n.to} to={n.to} end={n.end} className={navCls}>
                    <span className="text-xs opacity-60">{n.icon}</span>
                    {n.label}
                  </NavLink>
                ))}
              </nav>
            </div>
          </div>
        )}
      </header>

      {/* Main content */}
      <main className="max-w-screen-xl mx-auto px-4 py-6">
        {children}
      </main>
    </div>
  );
}

// ─── ESG Nav (legacy) ────────────────────────────────────────────────────────

function EsgNav() {
  const cls = ({ isActive }) =>
    `px-4 py-2 rounded-md text-sm font-medium transition-colors ${
      isActive
        ? 'bg-brand-900 text-white'
        : 'text-brand-100 hover:bg-brand-700 hover:text-white'
    }`;
  const loc = useLocation();
  return (
    <nav className="bg-brand-800 shadow-lg">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🌿</span>
          <span className="text-white font-bold text-lg">ESG Carbon Accounting</span>
          <span className="text-brand-200 text-xs ml-2 hidden sm:inline">SG · MY | GHG Protocol</span>
        </div>
        <div className="flex gap-1">
          <NavLink to="/" end className={cls}>Data Entry</NavLink>
          <NavLink to="/dashboard" className={cls}>Dashboard</NavLink>
          <NavLink to="/report" className={cls}>Report</NavLink>
          <Link
            to="/origination"
            className="ml-2 px-3 py-1.5 bg-ukmc-600 hover:bg-ukmc-500 text-white text-xs font-medium rounded-md transition-colors flex items-center"
          >
            ⬡ Origination →
          </Link>
        </div>
      </div>
    </nav>
  );
}

function NoData({ label }) {
  return (
    <div className="flex flex-col items-center justify-center py-28 text-gray-400">
      <span className="text-5xl mb-4">📋</span>
      <p className="text-lg font-medium text-gray-500">No calculation data yet</p>
      <p className="text-sm mt-1">{label}</p>
      <a href="/" className="mt-5 text-brand-700 underline text-sm">Go to Data Entry →</a>
    </div>
  );
}

// ─── App Content ──────────────────────────────────────────────────────────────

function AppContent() {
  const [calcResult, setCalcResult] = useState(null);
  const [formData,   setFormData]   = useState(null);
  const navigate = useNavigate();
  const loc = useLocation();

  const handleCalculate = (result, payload) => {
    setCalcResult(result);
    setFormData(payload);
    navigate('/dashboard');
  };

  // Origination routes use the dark layout
  if (loc.pathname.startsWith('/origination')) {
    return (
      <OriginationLayout>
        <Routes>
          <Route path="/origination"              element={<DealDashboard />} />
          <Route path="/origination/pipeline"     element={<Pipeline />} />
          <Route path="/origination/deals/:id"    element={<DealDetail />} />
          <Route path="/origination/intelligence" element={<IntelligenceFeed />} />
          <Route path="/origination/new-deal"     element={<NewDeal />} />
          <Route path="/origination/contacts"     element={<Contacts />} />
          <Route path="/origination/analytics"    element={<Analytics />} />
        </Routes>
      </OriginationLayout>
    );
  }

  // ESG routes use the legacy light layout
  return (
    <>
      <EsgNav />
      <main className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<DataEntry onCalculate={handleCalculate} />} />
          <Route
            path="/dashboard"
            element={
              calcResult
                ? <Dashboard result={calcResult} />
                : <NoData label="Complete a calculation on the Data Entry page first." />
            }
          />
          <Route
            path="/report"
            element={
              calcResult && formData
                ? <ReportPage result={calcResult} formData={formData} />
                : <NoData label="Complete a calculation on the Data Entry page first." />
            }
          />
        </Routes>
      </main>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}
