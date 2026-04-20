import { useState } from 'react';
import { BrowserRouter, NavLink, Route, Routes, useNavigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import DataEntry from './components/DataEntry';
import ReportPage from './components/ReportPage';

function NavBar() {
  const cls = ({ isActive }) =>
    `px-4 py-2 rounded-md text-sm font-medium transition-colors ${
      isActive
        ? 'bg-brand-900 text-white'
        : 'text-brand-100 hover:bg-brand-700 hover:text-white'
    }`;
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

// AppContent lives inside BrowserRouter so it can use useNavigate
function AppContent() {
  const [calcResult, setCalcResult] = useState(null);
  const [formData, setFormData] = useState(null);
  const navigate = useNavigate();

  const handleCalculate = (result, payload) => {
    setCalcResult(result);
    setFormData(payload);
    navigate('/dashboard');
  };

  return (
    <>
      <NavBar />
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
