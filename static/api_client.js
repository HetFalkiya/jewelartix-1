// ═══════════════════════════════════════════════════════════════
// JewelArtix Cloud API Client
// Replaces localStorage with real cloud database
// ═══════════════════════════════════════════════════════════════

const API_BASE = window.location.origin; // same server

// ── Generic API helpers ───────────────────────────────────────
async function apiGet(path) {
  try {
    const r = await fetch(`${API_BASE}${path}`);
    if (!r.ok) return null;
    return await r.json();
  } catch(e) { console.warn('API GET failed:', path, e); return null; }
}

async function apiPost(path, data) {
  try {
    const r = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return await r.json();
  } catch(e) { console.warn('API POST failed:', path, e); return null; }
}

async function apiDelete(path) {
  try {
    const r = await fetch(`${API_BASE}${path}`, { method: 'DELETE' });
    return await r.json();
  } catch(e) { console.warn('API DELETE failed:', path, e); return null; }
}

// ── Auto-save form state (debounced) ─────────────────────────
let _saveTimer = null;
function scheduleSave(tool, dataFn) {
  clearTimeout(_saveTimer);
  _saveTimer = setTimeout(async () => {
    const data = dataFn();
    await apiPost(`/api/formstate/${tool}`, data);
  }, 800); // save 800ms after last keystroke
}

// ── Restore form state ────────────────────────────────────────
async function cloudRestoreForm(tool, applyFn) {
  const data = await apiGet(`/api/formstate/${tool}`);
  if (data) applyFn(data);
}

// ── Save settings (labor + excel) ────────────────────────────
async function cloudSaveSettings(key, data) {
  return await apiPost(`/api/settings/${key}`, data);
}

async function cloudGetSettings(key) {
  return await apiGet(`/api/settings/${key}`);
}

async function cloudDeleteSettings(key) {
  return await apiDelete(`/api/settings/${key}`);
}

// ── Quotations ────────────────────────────────────────────────
async function cloudSaveQuotation(data) {
  return await apiPost('/api/quotations', data);
}

async function cloudGetQuotations() {
  return await apiGet('/api/quotations') || [];
}

async function cloudGetQuotation(quotNo) {
  return await apiGet(`/api/quotations/${encodeURIComponent(quotNo)}`);
}

async function cloudDeleteQuotation(quotNo) {
  return await apiDelete(`/api/quotations/${encodeURIComponent(quotNo)}`);
}
