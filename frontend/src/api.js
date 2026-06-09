// API base URL — empty string routes through the Vite dev proxy (/api, /dr → :8000)
const BASE = import.meta.env.VITE_API_URL ?? '';

async function _req(method, path, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(`${BASE}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? `${method} ${path} failed (${res.status})`);
  }
  return res;
}

const _get  = (path)        => _req('GET',    path);
const _post = (path, body)  => _req('POST',   path, body);
const _del  = (path)        => _req('DELETE', path);

// ── ESG Carbon ───────────────────────────────────────────────────────────────

export async function calculateEmissions(payload) {
  return (await _post('/api/calculate', payload)).json();
}

export async function downloadReport(payload) {
  return (await _post('/api/report', payload)).blob();
}

export async function getCompanies() {
  return (await _get('/api/companies')).json();
}

// ── Deal Radar ────────────────────────────────────────────────────────────────

export const dr = {
  getCompanies:       ()            => _get('/dr/companies').then(r => r.json()),
  addCompany:         (data)        => _post('/dr/companies', data).then(r => r.json()),
  removeCompany:      (id)          => _del(`/dr/companies/${id}`),

  getInferencesToday: (minScore=40) => _get(`/dr/inferences/today?min_score=${minScore}`).then(r => r.json()),
  getInferences:      (days=7, min=0) => _get(`/dr/inferences?days=${days}&min_score=${min}`).then(r => r.json()),

  getSignals:         (companyId, days=30) => _get(`/dr/signals/${companyId}?days=${days}`).then(r => r.json()),

  submitFeedback:     (id, outcome, notes='') =>
    _post(`/dr/feedback/${id}`, { outcome, notes }).then(r => r.json()),

  getBacktest:        ()  => _get('/dr/backtest/simulation').then(r => r.json()),
  getFundingEvents:   ()  => _get('/dr/funding-events').then(r => r.json()),

  runSignals:         ()  => _post('/dr/run/signals').then(r => r.json()),
  runEnrichment:      ()  => _post('/dr/run/enrichment').then(r => r.json()),
  runInference:       ()  => _post('/dr/run/inference').then(r => r.json()),
  runDelivery:        ()  => _post('/dr/run/delivery').then(r => r.json()),

  previewDigest:      ()  => _get('/dr/digest/preview').then(r => r.json()),
  scoreSignals:       (types) => _post('/dr/score', { signal_types: types }).then(r => r.json()),
};
