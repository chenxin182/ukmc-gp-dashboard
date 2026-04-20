// API base URL — empty string routes through the Vite dev proxy (/api → :8000)
const BASE = import.meta.env.VITE_API_URL ?? '';

async function _post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? 'Request failed');
  }
  return res;
}

export async function calculateEmissions(payload) {
  const res = await _post('/api/calculate', payload);
  return res.json();
}

export async function downloadReport(payload) {
  const res = await _post('/api/report', payload);
  return res.blob();
}

export async function getCompanies() {
  const res = await fetch(`${BASE}/api/companies`);
  if (!res.ok) throw new Error('Failed to fetch companies');
  return res.json();
}
