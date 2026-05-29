// API base URL — empty string routes through the Vite dev proxy (/api → :8000)
const BASE = import.meta.env.VITE_API_URL ?? '';

// ─── Generic helpers ────────────────────────────────────────────────────────

async function _req(method, path, body) {
  const opts = {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    ...(body ? { body: JSON.stringify(body) } : {}),
  };
  const res = await fetch(`${BASE}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? 'Request failed');
  }
  return res;
}

const _get  = (path)        => _req('GET',    path);
const _post = (path, body)  => _req('POST',   path, body);
const _put  = (path, body)  => _req('PUT',    path, body);
const _del  = (path)        => _req('DELETE', path);

// ─── Deal Origination API ───────────────────────────────────────────────────

export async function getDeals(params = {}) {
  const qs = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v != null && v !== ''))
  ).toString();
  const res = await _get(`/api/deals${qs ? `?${qs}` : ''}`);
  return res.json();
}

export async function getDeal(id) {
  const res = await _get(`/api/deals/${id}`);
  return res.json();
}

export async function createDeal(payload) {
  const res = await _post('/api/deals', payload);
  return res.json();
}

export async function updateDeal(id, payload) {
  const res = await _put(`/api/deals/${id}`, payload);
  return res.json();
}

export async function deleteDeal(id) {
  await _del(`/api/deals/${id}`);
}

export async function changeDealStage(id, stage) {
  const res = await _post(`/api/deals/${id}/stage`, { stage });
  return res.json();
}

export async function getPipelineStats() {
  const res = await _get('/api/pipeline/stats');
  return res.json();
}

export async function getSignals(params = {}) {
  const qs = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v != null && v !== ''))
  ).toString();
  const res = await _get(`/api/signals${qs ? `?${qs}` : ''}`);
  return res.json();
}

export async function convertSignalToDeal(signalId) {
  const res = await _post(`/api/signals/${signalId}/convert`, {});
  return res.json();
}

export async function getContacts(params = {}) {
  const qs = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v != null && v !== ''))
  ).toString();
  const res = await _get(`/api/contacts${qs ? `?${qs}` : ''}`);
  return res.json();
}

export async function createContact(payload) {
  const res = await _post('/api/contacts', payload);
  return res.json();
}

export async function runIntelligence(params = {}) {
  const res = await _post('/api/intelligence/run', params);
  return res.json();
}

export async function getAnalytics() {
  const res = await _get('/api/analytics');
  return res.json();
}

// ─── ESG Carbon API (legacy) ────────────────────────────────────────────────

export async function calculateEmissions(payload) {
  const res = await _post('/api/calculate', payload);
  return res.json();
}

export async function downloadReport(payload) {
  const res = await _post('/api/report', payload);
  return res.blob();
}

export async function getCompanies() {
  const res = await _get('/api/companies');
  return res.json();
}
