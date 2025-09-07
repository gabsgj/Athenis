const cfg = (window.APP_CONFIG || {});
const API_BASE = cfg.API_BASE_URL || '/api/v1';
const API_CORE = '/api';
const GOFR_BASE = cfg.GOFR_BASE_URL || 'http://localhost:8090';
const REQUIRE_KEY = !!cfg.REQUIRE_API_KEY;

const ui = {
  // legacy ids (kept for backward compat)
  apiKey: document.getElementById('apiKey') || document.getElementById('api-key'),
  task: document.getElementById('task') || document.getElementById('task-select'),
  lang: document.getElementById('language') || document.getElementById('language-select'),
  text: document.getElementById('textInput') || document.getElementById('text-input'),
  original: document.getElementById('original') || document.getElementById('original-text'),
  plain: document.getElementById('plain') || document.getElementById('output-text'),
  summary: document.getElementById('summary') || document.getElementById('summary-text'),
  risks: document.getElementById('risks') || document.getElementById('risk-analysis'),
  search: document.getElementById('searchOriginal'),
  spinner: document.getElementById('spinner'),
  toasts: document.getElementById('toasts'),
  analyzeBtn: document.getElementById('analyzeBtn') || document.getElementById('analyze-btn'),
  streamBtn: document.getElementById('streamBtn') || document.getElementById('stream-btn'),
  uploadBtn: document.getElementById('uploadBtn'),
  largeDoc: document.getElementById('largeDoc'),
  printBtn: document.getElementById('printBtn'),
  exportBtn: document.getElementById('exportBtn'),
  tabs: {
    upload: document.getElementById('tab-upload') || document.getElementById('upload-tab'),
    paste: document.getElementById('tab-paste') || document.getElementById('paste-tab'),
  },
  panels: {
    upload: document.getElementById('panel-upload') || document.getElementById('upload-content'),
    paste: document.getElementById('panel-paste') || document.getElementById('paste-content'),
  },
  counts: {
    chars: document.getElementById('char-count')
  }
};

function toast(msg, type = 'info', ms = 3000) {
  if (!ui.toasts) { console[type === 'error' ? 'error' : 'log'](msg); return; }
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  ui.toasts.appendChild(el);
  setTimeout(() => el.classList.add('show'));
  setTimeout(() => {
    el.classList.remove('show');
    setTimeout(() => el.remove(), 300);
  }, ms);
}

function headersJSON() {
  const h = { 'Content-Type': 'application/json' };
  if (ui.apiKey && ui.apiKey.value) {
    h['x-api-key'] = ui.apiKey.value; // backend expects this
    // optional auth mirror
    h['Authorization'] = `Bearer ${ui.apiKey.value}`;
  }
  return h;
}

function headersForm() {
  const h = {};
  if (ui.apiKey && ui.apiKey.value) {
    h['x-api-key'] = ui.apiKey.value;
    h['Authorization'] = `Bearer ${ui.apiKey.value}`;
  }
  return h;
}

// Tabs
function selectTab(name) {
  const isUpload = name === 'upload';
  ui.tabs.upload.classList.toggle('active', isUpload);
  ui.tabs.upload.setAttribute('aria-selected', String(isUpload));
  ui.tabs.paste.classList.toggle('active', !isUpload);
  ui.tabs.paste.setAttribute('aria-selected', String(!isUpload));
  ui.panels.upload.classList.toggle('hidden', !isUpload);
  ui.panels.paste.classList.toggle('hidden', isUpload);
}
ui.tabs.upload && ui.tabs.upload.addEventListener('click', () => selectTab('upload'));
ui.tabs.paste && ui.tabs.paste.addEventListener('click', () => selectTab('paste'));

// Upload
ui.uploadBtn && ui.uploadBtn.addEventListener('click', async () => {
  try {
    const file = document.getElementById('fileInput').files[0];
    if (!file) return toast('Select a file', 'warn');
    if (file.size > 20 * 1024 * 1024) return toast('Max file size is 20MB', 'error');
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${GOFR_BASE}/ingest`, {
      method: 'POST',
      headers: headersForm(),
      body: form,
    });
    if (!res.ok) {
      if (res.status === 401) return toast('Unauthorized (API key?)', 'error');
      if (res.status === 429) return toast('Rate limited. Try later.', 'error');
      return toast(`Upload failed: HTTP ${res.status}`, 'error');
    }
        const data = await res.json();
        const text = (data.text) || (data.chunks?.map(c => c.text).join('\n') || '');
    ui.text.value = text;
    setOriginal(text);
    toast('Uploaded and loaded text', 'success');
        if (ui.largeDoc.checked && Array.isArray(data.chunks) && data.chunks.length > 1) {
          toast(`Detected ${data.chunks.length} chunks. Consider "Full Analysis".`, 'info', 5000);
        }
  } catch (e) {
    toast(String(e), 'error');
  }
});

function setOriginal(text) {
  if (!ui.original) return;
  const tag = (ui.original.tagName || '').toLowerCase();
  if (tag === 'pre' || tag === 'textarea') {
    ui.original.textContent = text;
    return;
  }
  ui.original.innerHTML = '';
  const div = document.createElement('div');
  div.textContent = text;
  ui.original.appendChild(div);
}

ui.text && ui.text.addEventListener('input', () => setOriginal(ui.text.value));
// live char count for new UI
ui.text && ui.text.addEventListener('input', () => {
  if (ui.counts && ui.counts.chars) ui.counts.chars.textContent = String(ui.text.value.length);
});
ui.search && ui.search.addEventListener('input', () => {
  const q = ui.search.value.toLowerCase();
  const text = ui.text.value;
  if (!q) return setOriginal(text);
  // simple highlight
  const frag = document.createElement('div');
  let i = 0;
  const lower = text.toLowerCase();
  while (i < text.length) {
    const j = lower.indexOf(q, i);
    if (j === -1) { frag.appendChild(document.createTextNode(text.slice(i))); break; }
function escapeHtml(s){
  return s.replace(/[&<>"']/g, c => ({
    '&':'&amp;',
    '<':'&lt;',
    '>':'&gt;',
    '"':'&quot;',
    "'":'&#39;'
  }[c]));
}
    const mark = document.createElement('mark');
    mark.textContent = text.slice(j, j + q.length);
    frag.appendChild(mark);
    i = j + q.length;
  }
  ui.original.innerHTML = '';
  ui.original.appendChild(frag);
});

let currentStream = null;
async function analyzeOnce() {
  try {
    const text = ui.text.value.trim();
    if (!text) return toast('No text to analyze', 'warn');
    setBusy(true);
    const task = ui.task.value;
    // Use richer endpoint for full or risk
    if (task === 'full' || task === 'risk') {
      const res = await fetch(`${API_CORE}/full-analysis`, {
        method: 'POST', headers: headersJSON(),
        body: JSON.stringify({ text })
      });
      const data = await res.json();
      if (!res.ok || !data || data.ok === false) { handleHttpError(res, data); return; }
      const r = data.result || {};
      ui.plain.textContent = (r.simplified || '').trim();
      if (ui.summary) ui.summary.textContent = r.summary || '';
      renderRisks(r.risk || [], ui.text.value);
    } else {
      const res = await fetch(`${API_BASE}/inference`, {
        method: 'POST', headers: headersJSON(),
        body: JSON.stringify({ text, task, language: ui.lang.value })
      });
      const data = await res.json();
      if (!res.ok) { handleHttpError(res, data); return; }
      // v1 returns { ok, task, result: string }
      const out = data.result || '';
      if (task === 'summarize') {
        if (ui.summary) ui.summary.textContent = out;
      } else {
        ui.plain.textContent = out;
      }
    }
    toast && toast('Analysis complete', 'success');
  } catch (e) {
    toast(String(e), 'error');
  } finally {
    setBusy(false);
  }
}

async function streamSimplify() {
  if (currentStream) { currentStream.abort(); currentStream = null; ui.streamBtn.textContent = 'Stream Simplify'; return; }
  try {
    const text = ui.text.value.trim();
    if (!text) return toast('No text to stream', 'warn');
    setBusy(true);
    ui.plain.textContent = '';
    ui.streamBtn.textContent = 'Cancel';
    const ctrl = new AbortController();
    currentStream = ctrl;
  // Hit core simplify with streaming
  const url = `${API_CORE}/simplify?stream=1`;
  const headers = headersJSON();
  headers['Accept'] = 'text/event-stream';
  const res = await fetch(url, { method: 'POST', headers, signal: ctrl.signal, body: JSON.stringify({ text }) });
    if (!res.ok) {
      const data = await res.text();
      handleHttpError(res, data); return;
    }
    if (!res.body) return;
    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buf = '';
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const parts = buf.split('\n\n');
      for (let i = 0; i < parts.length - 1; i++) handleSSE(parts[i]);
      buf = parts[parts.length - 1];
    }
    toast('Stream finished', 'success');
  } catch (e) {
    if (e.name !== 'AbortError') toast(String(e), 'error');
  } finally {
    setBusy(false);
    currentStream = null;
    ui.streamBtn.textContent = 'Stream Simplify';
  }
}

function handleSSE(chunk) {
  const lines = chunk.split('\n');
  let event = 'message'; let data = '';
  for (const l of lines) {
    if (l.startsWith('event:')) event = l.replace('event:', '').trim();
    if (l.startsWith('data:')) data += l.replace('data:', '').trim();
  }
  if (event === 'simplify' || event === 'token' || event === 'chunk') ui.plain.textContent += data;
}

function renderResult(data) {
  // support legacy richer shape
  if (!data) return;
  if (data.overview || data.plain_language) {
    if (ui.summary) ui.summary.textContent = data.overview || '';
    ui.plain.textContent = (data.plain_language || '').trim();
    renderRisks(data.risks_detected || [], ui.text.value);
  }
}

function renderRisks(risks, sourceText) {
  if (!ui.risks) return;
  ui.risks.innerHTML = '';
  if (!Array.isArray(risks) || risks.length === 0) {
    ui.risks.innerHTML = '<div class="p-3 text-gray-500 text-xs">No risks detected.</div>';
    return;
  }
  // If legacy risks table exists (role rowgroup), fill rows; else build cards
  const legacy = ui.risks.getAttribute('role') === 'rowgroup';
  if (legacy) {
    risks.forEach((r) => {
      const row = document.createElement('div');
      row.className = 'risk-row'; row.setAttribute('role', 'row');
      const sev = (r.severity || 'medium').toLowerCase();
      const cells = [
        cell(r.type || ''),
        cell(`<span class="badge ${sev}">${sev}</span>`),
        cell(escapeHtml(r.clause_excerpt || '')),
        cell(escapeHtml(r.explanation || '')),
        cell(escapeHtml(r.suggested_action || '')),
      ];
      cells.forEach(c => row.appendChild(c));
      row.addEventListener('click', () => highlightExcerpt(r.clause_excerpt || '', sourceText));
      ui.risks.appendChild(row);
    });
  } else {
    const list = document.createElement('div');
    list.className = 'divide-y divide-gray-200';
    risks.forEach((r) => {
      const sev = (r.severity || 'medium').toLowerCase();
      const item = document.createElement('div');
      item.className = 'p-3 text-sm';
      item.innerHTML = `
        <div class="flex items-start justify-between gap-2">
          <div>
            <div class="font-semibold text-gray-800">${escapeHtml(r.type || 'Risk')}</div>
            <div class="text-gray-600">${escapeHtml(r.explanation || '')}</div>
            ${r.suggested_action ? `<div class="text-gray-700 mt-1"><span class="font-medium">Suggestion:</span> ${escapeHtml(r.suggested_action)}</div>` : ''}
            ${r.clause_excerpt ? `<div class="mt-2 text-xs text-gray-500">Excerpt: “${escapeHtml(r.clause_excerpt)}”</div>` : ''}
          </div>
          <span class="px-2 py-0.5 rounded text-xs bg-gray-100 border">${sev}</span>
        </div>`;
      item.addEventListener('click', () => highlightExcerpt(r.clause_excerpt || '', sourceText));
      list.appendChild(item);
    });
    ui.risks.appendChild(list);
  }
}

function cell(html) { const d = document.createElement('div'); d.setAttribute('role','cell'); d.innerHTML = html; return d; }
function escapeHtml(s){ return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c])); }

function highlightExcerpt(excerpt, source){
  if (!excerpt) return;
  const idx = source.indexOf(excerpt);
  if (idx === -1) { toast('Excerpt not found in original', 'warn'); return; }
  // rebuild original with a single highlight mark
  const before = source.slice(0, idx);
  const after = source.slice(idx + excerpt.length);
  const frag = document.createElement('div');
  frag.appendChild(document.createTextNode(before));
  const mark = document.createElement('mark'); mark.className = 'hl'; mark.textContent = excerpt; frag.appendChild(mark);
  frag.appendChild(document.createTextNode(after));
  ui.original.innerHTML = ''; ui.original.appendChild(frag);
  mark.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function setBusy(b){ if (!ui.spinner) return; ui.spinner.hidden = !b; ui.spinner.setAttribute('aria-busy', String(b)); }

function handleHttpError(res, body){
  const msg = typeof body === 'string' ? body : (body && (body.message || body.error)) || `HTTP ${res.status}`;
  if (res.status === 401) toast('Unauthorized (API key?)', 'error');
  else if (res.status === 429) toast(`Rate limited. Retry later.`, 'error');
  else toast(msg, 'error');
}

// Export & Print
ui.exportBtn && ui.exportBtn.addEventListener('click', () => {
  const report = {
    task: ui.task.value,
    language: ui.lang.value,
    original: ui.text.value,
    summary: ui.summary.textContent,
    plain: ui.plain.textContent,
  };
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = `report-${Date.now()}.json`; a.click(); URL.revokeObjectURL(url);
});
ui.printBtn && ui.printBtn.addEventListener('click', () => window.print());

// Analyze & Stream
ui.analyzeBtn && ui.analyzeBtn.addEventListener('click', analyzeOnce);
ui.streamBtn && ui.streamBtn.addEventListener('click', streamSimplify);

// Default to paste tab
if (ui.tabs.upload || ui.tabs.paste) selectTab('paste'); else setActiveTab('paste');

// -------------
// New UI helpers (global for onclick in HTML)
// -------------
function getApiHeaders() {
  const h = { 'Content-Type': 'application/json' };
  if (ui.apiKey && ui.apiKey.value) h['X-API-Key'] = ui.apiKey.value;
  return h;
}

function setActiveTab(tab) {
  const isUpload = tab === 'upload';
  if (ui.tabs.upload) ui.tabs.upload.classList.toggle('bg-white', isUpload);
  if (ui.tabs.paste) ui.tabs.paste.classList.toggle('bg-white', !isUpload);
  if (ui.panels.upload) ui.panels.upload.classList.toggle('hidden', !isUpload);
  if (ui.panels.paste) ui.panels.paste.classList.toggle('hidden', isUpload);
}

async function handleFileUpload(ev) {
  try {
    const file = ev && ev.target && ev.target.files ? ev.target.files[0] : null;
    if (!file) return;
    if (file.size > 20 * 1024 * 1024) { alert('Max 20MB'); return; }
    const form = new FormData(); form.append('file', file);
    const res = await fetch(`${GOFR_BASE}/ingest`, { method:'POST', headers: (ui.apiKey?.value ? {'X-API-Key': ui.apiKey.value} : {}), body: form });
    if (!res.ok) { alert(`Upload failed: ${res.status}`); return; }
    const data = await res.json();
    const text = (data.text) || (data.chunks?.map(c => c.text).join('\n') || '');
    if (ui.text) ui.text.value = text;
    if (ui.original) ui.original.textContent = text;
    if (ui.counts && ui.counts.chars) ui.counts.chars.textContent = String(text.length);
  } catch (e) {
    alert(String(e));
  }
}

async function handleAnalyze(){ return analyzeOnce(); }
async function handleStreamSimplify(){ return streamSimplify(); }

function exportJSON(){
  const report = {
    task: ui.task?.value,
    language: ui.lang?.value,
    original: ui.text?.value || '',
    summary: ui.summary?.textContent || '',
    plain: ui.plain?.textContent || ''
  };
  const blob = new Blob([JSON.stringify(report, null, 2)], {type:'application/json'});
  const url = URL.createObjectURL(blob); const a = document.createElement('a');
  a.href = url; a.download = `report-${Date.now()}.json`; a.click(); URL.revokeObjectURL(url);
}

function printReport(){ window.print(); }

function scrollToSection(id){ const el = document.getElementById(id); if (el) el.scrollIntoView({behavior:'smooth'}); }
function scrollToApp(){ scrollToSection('app-section'); }

// expose for inline handlers
window.setActiveTab = setActiveTab;
window.handleFileUpload = handleFileUpload;
window.handleAnalyze = handleAnalyze;
window.handleStreamSimplify = handleStreamSimplify;
window.exportJSON = exportJSON;
window.printReport = printReport;
window.scrollToSection = scrollToSection;
window.scrollToApp = scrollToApp;



// hhconst cfg = (window.APP_CONFIG || {});
// const API_BASE = cfg.API_BASE_URL || '/api/v1';
// const GOFR_BASE = cfg.GOFR_BASE_URL || 'http://localhost:9090';
// const REQUIRE_KEY = !!cfg.REQUIRE_API_KEY;

// const ui = {
//   apiKey: document.getElementById('apiKey'),
//   task: document.getElementById('task'),
//   lang: document.getElementById('language'),
//   text: document.getElementById('textInput'),
//   original: document.getElementById('original'),
//   plain: document.getElementById('plain'),
//   summary: document.getElementById('summary'),
//   risks: document.getElementById('risks'),
//   search: document.getElementById('searchOriginal'),
//   spinner: document.getElementById('spinner'),
//   toasts: document.getElementById('toasts'),
//   analyzeBtn: document.getElementById('analyzeBtn'),
//   streamBtn: document.getElementById('streamBtn'),
//   uploadBtn: document.getElementById('uploadBtn'),
//   largeDoc: document.getElementById('largeDoc'),
//   printBtn: document.getElementById('printBtn'),
//   exportBtn: document.getElementById('exportBtn'),
//   tabs: {
//     upload: document.getElementById('tab-upload'),
//     paste: document.getElementById('tab-paste'),
//   },
//   panels: {
//     upload: document.getElementById('panel-upload'),
//     paste: document.getElementById('panel-paste'),
//   },
// };

// function toast(msg, type = 'info', ms = 3000) {
//   const el = document.createElement('div');
//   el.className = `toast ${type}`;
//   el.textContent = msg;
//   ui.toasts.appendChild(el);
//   setTimeout(() => el.classList.add('show'));
//   setTimeout(() => {
//     el.classList.remove('show');
//     setTimeout(() => el.remove(), 300);
//   }, ms);
// }

// function headersJSON() {
//   const h = { 'Content-Type': 'application/json' };
//   if (REQUIRE_KEY && ui.apiKey.value) {
//     h['Authorization'] = `Bearer ${ui.apiKey.value}`;
//     h['x-api-key'] = ui.apiKey.value; // backend expects this; send both
//   }
//   return h;
// }

// function headersForm() {
//   const h = {};
//   if (REQUIRE_KEY && ui.apiKey.value) {
//     h['Authorization'] = `Bearer ${ui.apiKey.value}`;
//     h['x-api-key'] = ui.apiKey.value;
//   }
//   return h;
// }

// // Tabs
// function selectTab(name) {
//   const isUpload = name === 'upload';
//   ui.tabs.upload.classList.toggle('active', isUpload);
//   ui.tabs.upload.setAttribute('aria-selected', String(isUpload));
//   ui.tabs.paste.classList.toggle('active', !isUpload);
//   ui.tabs.paste.setAttribute('aria-selected', String(!isUpload));
//   ui.panels.upload.classList.toggle('hidden', !isUpload);
//   ui.panels.paste.classList.toggle('hidden', isUpload);
// }
// ui.tabs.upload.addEventListener('click', () => selectTab('upload'));
// ui.tabs.paste.addEventListener('click', () => selectTab('paste'));

// // Upload
// ui.uploadBtn.addEventListener('click', async () => {
//   try {
//     const file = document.getElementById('fileInput').files[0];
//     if (!file) return toast('Select a file', 'warn');
//     if (file.size > 20 * 1024 * 1024) return toast('Max file size is 20MB', 'error');
//     const form = new FormData();
//     form.append('file', file);
//     const res = await fetch(`${GOFR_BASE}/ingest`, {
//       method: 'POST',
//       headers: headersForm(),
//       body: form,
//     });
//     if (!res.ok) {
//       if (res.status === 401) return toast('Unauthorized (API key?)', 'error');
//       if (res.status === 429) return toast('Rate limited. Try later.', 'error');
//       return toast(`Upload failed: HTTP ${res.status}`, 'error');
//     }
//         const data = await res.json();
//         const text = (data.text) || (data.chunks?.map(c => c.text).join('\n') || '');
//     ui.text.value = text;
//     setOriginal(text);
//     toast('Uploaded and loaded text', 'success');
//         if (ui.largeDoc.checked && Array.isArray(data.chunks) && data.chunks.length > 1) {
//           toast(`Detected ${data.chunks.length} chunks. Consider "Full Analysis".`, 'info', 5000);
//         }
//   } catch (e) {
//     toast(String(e), 'error');
//   }
// });

// function setOriginal(text) {
//   ui.original.innerHTML = '';
//   const div = document.createElement('div');
//   div.textContent = text;
//   ui.original.appendChild(div);
// }

// ui.text.addEventListener('input', () => setOriginal(ui.text.value));
// ui.search.addEventListener('input', () => {
//   const q = ui.search.value.toLowerCase();
//   const text = ui.text.value;
//   if (!q) return setOriginal(text);
//   // simple highlight
//   const frag = document.createElement('div');
//   let i = 0;
//   const lower = text.toLowerCase();
//   while (i < text.length) {
//     const j = lower.indexOf(q, i);
//     if (j === -1) { frag.appendChild(document.createTextNode(text.slice(i))); break; }
// function escapeHtml(s){
//   return s.replace(/[&<>"']/g, c => ({
//     '&':'&amp;',
//     '<':'&lt;',
//     '>':'&gt;',
//     '"':'&quot;',
//     "'":'&#39;'
//   }[c]));
// }
//     const mark = document.createElement('mark');
//     mark.textContent = text.slice(j, j + q.length);
//     frag.appendChild(mark);
//     i = j + q.length;
//   }
//   ui.original.innerHTML = '';
//   ui.original.appendChild(frag);
// });

// let currentStream = null;
// async function analyzeOnce() {
//   try {
//     const text = ui.text.value.trim();
//     if (!text) return toast('No text to analyze', 'warn');
//     setBusy(true);
//     const task = ui.task.value === 'full' ? 'simplify' : ui.task.value;
//     const res = await fetch(`${API_BASE}/inference`, {
//       method: 'POST', headers: headersJSON(),
//       body: JSON.stringify({ text, task, language: ui.lang.value })
//     });
//     const data = await res.json();
//     if (!res.ok) {
//       handleHttpError(res, data); return;
//     }
//     renderResult(data);
//     toast('Analysis complete', 'success');
//   } catch (e) {
//     toast(String(e), 'error');
//   } finally {
//     setBusy(false);
//   }
// }

// async function streamSimplify() {
//   if (currentStream) { currentStream.abort(); currentStream = null; ui.streamBtn.textContent = 'Stream Simplify'; return; }
//   try {
//     const text = ui.text.value.trim();
//     if (!text) return toast('No text to stream', 'warn');
//     setBusy(true);
//     ui.plain.textContent = '';
//     ui.streamBtn.textContent = 'Cancel';
//     const ctrl = new AbortController();
//     currentStream = ctrl;
//     const res = await fetch(`${API_BASE}/stream`, {
//       method: 'POST', headers: headersJSON(), signal: ctrl.signal,
//       body: JSON.stringify({ text, task: 'simplify', language: ui.lang.value })
//     });
//     if (!res.ok) {
//       const data = await res.text();
//       handleHttpError(res, data); return;
//     }
//     if (!res.body) return;
//     const reader = res.body.getReader();
//     const decoder = new TextDecoder('utf-8');
//     let buf = '';
//     while (true) {
//       const { value, done } = await reader.read();
//       if (done) break;
//       buf += decoder.decode(value, { stream: true });
//       const parts = buf.split('\n\n');
//       for (let i = 0; i < parts.length - 1; i++) handleSSE(parts[i]);
//       buf = parts[parts.length - 1];
//     }
//     toast('Stream finished', 'success');
//   } catch (e) {
//     if (e.name !== 'AbortError') toast(String(e), 'error');
//   } finally {
//     setBusy(false);
//     currentStream = null;
//     ui.streamBtn.textContent = 'Stream Simplify';
//   }
// }

// function handleSSE(chunk) {
//   const lines = chunk.split('\n');
//   let event = 'message'; let data = '';
//   for (const l of lines) {
//     if (l.startsWith('event:')) event = l.replace('event:', '').trim();
//     if (l.startsWith('data:')) data += l.replace('data:', '').trim();
//   }
//   if (event === 'token') ui.plain.textContent += data;
// }

// function renderResult(data) {
//   ui.summary.textContent = data.overview || '';
//   ui.plain.textContent = (data.plain_language || '').trim();
//   renderRisks(data.risks_detected || [], ui.text.value);
// }

// function renderRisks(risks, sourceText) {
//   ui.risks.innerHTML = '';
//   risks.forEach((r, idx) => {
//     const row = document.createElement('div');
//     row.className = 'risk-row'; row.setAttribute('role', 'row');
//     const sev = (r.severity || 'medium').toLowerCase();
//     const cells = [
//       cell(r.type || ''),
//       cell(`<span class="badge ${sev}">${sev}</span>`),
//       cell(escapeHtml(r.clause_excerpt || '')),
//       cell(escapeHtml(r.explanation || '')),
//       cell(escapeHtml(r.suggested_action || '')),
//     ];
//     cells.forEach(c => row.appendChild(c));
//     row.addEventListener('click', () => highlightExcerpt(r.clause_excerpt || '', sourceText));
//     ui.risks.appendChild(row);
//   });
// }

// function cell(html) { const d = document.createElement('div'); d.setAttribute('role','cell'); d.innerHTML = html; return d; }
// function escapeHtml(s){ return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c])); }

// function highlightExcerpt(excerpt, source){
//   if (!excerpt) return;
//   const idx = source.indexOf(excerpt);
//   if (idx === -1) { toast('Excerpt not found in original', 'warn'); return; }
//   // rebuild original with a single highlight mark
//   const before = source.slice(0, idx);
//   const after = source.slice(idx + excerpt.length);
//   const frag = document.createElement('div');
//   frag.appendChild(document.createTextNode(before));
//   const mark = document.createElement('mark'); mark.className = 'hl'; mark.textContent = excerpt; frag.appendChild(mark);
//   frag.appendChild(document.createTextNode(after));
//   ui.original.innerHTML = ''; ui.original.appendChild(frag);
//   mark.scrollIntoView({ behavior: 'smooth', block: 'center' });
// }

// function setBusy(b){ ui.spinner.hidden = !b; ui.spinner.setAttribute('aria-busy', String(b)); }

// function handleHttpError(res, body){
//   const msg = typeof body === 'string' ? body : (body && (body.message || body.error)) || `HTTP ${res.status}`;
//   if (res.status === 401) toast('Unauthorized (API key?)', 'error');
//   else if (res.status === 429) toast(`Rate limited. Retry later.`, 'error');
//   else toast(msg, 'error');
// }

// // Export & Print
// ui.exportBtn.addEventListener('click', () => {
//   const report = {
//     task: ui.task.value,
//     language: ui.lang.value,
//     original: ui.text.value,
//     summary: ui.summary.textContent,
//     plain: ui.plain.textContent,
//   };
//   const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
//   const url = URL.createObjectURL(blob);
//   const a = document.createElement('a'); a.href = url; a.download = `report-${Date.now()}.json`; a.click(); URL.revokeObjectURL(url);
// });
// ui.printBtn.addEventListener('click', () => window.print());

// // Analyze & Stream
// ui.analyzeBtn.addEventListener('click', analyzeOnce);
// ui.streamBtn.addEventListener('click', streamSimplify);

// // Default to paste tab
// selectTab('paste');
