const cfg = (window.APP_CONFIG || {});
const API_BASE = cfg.API_BASE_URL || '/api/v1';
const GOFR_BASE = cfg.GOFR_BASE_URL || 'http://localhost:9090';
const REQUIRE_KEY = !!cfg.REQUIRE_API_KEY;

const ui = {
  apiKey: document.getElementById('apiKey'),
  task: document.getElementById('task'),
  lang: document.getElementById('language'),
  text: document.getElementById('textInput'),
  original: document.getElementById('original'),
  plain: document.getElementById('plain'),
  summary: document.getElementById('summary'),
  risks: document.getElementById('risks'),
  search: document.getElementById('searchOriginal'),
  spinner: document.getElementById('spinner'),
  toasts: document.getElementById('toasts'),
  analyzeBtn: document.getElementById('analyzeBtn'),
  streamBtn: document.getElementById('streamBtn'),
  uploadBtn: document.getElementById('uploadBtn'),
  largeDoc: document.getElementById('largeDoc'),
  printBtn: document.getElementById('printBtn'),
  exportBtn: document.getElementById('exportBtn'),
  tabs: {
    upload: document.getElementById('tab-upload'),
    paste: document.getElementById('tab-paste'),
  },
  panels: {
    upload: document.getElementById('panel-upload'),
    paste: document.getElementById('panel-paste'),
  },
};

function toast(msg, type = 'info', ms = 3000) {
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
  if (REQUIRE_KEY && ui.apiKey.value) {
    h['Authorization'] = `Bearer ${ui.apiKey.value}`;
    h['x-api-key'] = ui.apiKey.value; // backend expects this; send both
  }
  return h;
}

function headersForm() {
  const h = {};
  if (REQUIRE_KEY && ui.apiKey.value) {
    h['Authorization'] = `Bearer ${ui.apiKey.value}`;
    h['x-api-key'] = ui.apiKey.value;
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
ui.tabs.upload.addEventListener('click', () => selectTab('upload'));
ui.tabs.paste.addEventListener('click', () => selectTab('paste'));

// Upload
ui.uploadBtn.addEventListener('click', async () => {
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
  ui.original.innerHTML = '';
  const div = document.createElement('div');
  div.textContent = text;
  ui.original.appendChild(div);
}

ui.text.addEventListener('input', () => setOriginal(ui.text.value));
ui.search.addEventListener('input', () => {
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
    const task = ui.task.value === 'full' ? 'simplify' : ui.task.value;
    const res = await fetch(`${API_BASE}/inference`, {
      method: 'POST', headers: headersJSON(),
      body: JSON.stringify({ text, task, language: ui.lang.value })
    });
    const data = await res.json();
    if (!res.ok) {
      handleHttpError(res, data); return;
    }
    renderResult(data);
    toast('Analysis complete', 'success');
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
    const res = await fetch(`${API_BASE}/stream`, {
      method: 'POST', headers: headersJSON(), signal: ctrl.signal,
      body: JSON.stringify({ text, task: 'simplify', language: ui.lang.value })
    });
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
  if (event === 'token') ui.plain.textContent += data;
}

function renderResult(data) {
  ui.summary.textContent = data.overview || '';
  ui.plain.textContent = (data.plain_language || '').trim();
  renderRisks(data.risks_detected || [], ui.text.value);
}

function renderRisks(risks, sourceText) {
  ui.risks.innerHTML = '';
  risks.forEach((r, idx) => {
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

function setBusy(b){ ui.spinner.hidden = !b; ui.spinner.setAttribute('aria-busy', String(b)); }

function handleHttpError(res, body){
  const msg = typeof body === 'string' ? body : (body && (body.message || body.error)) || `HTTP ${res.status}`;
  if (res.status === 401) toast('Unauthorized (API key?)', 'error');
  else if (res.status === 429) toast(`Rate limited. Retry later.`, 'error');
  else toast(msg, 'error');
}

// Export & Print
ui.exportBtn.addEventListener('click', () => {
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
ui.printBtn.addEventListener('click', () => window.print());

// Analyze & Stream
ui.analyzeBtn.addEventListener('click', analyzeOnce);
ui.streamBtn.addEventListener('click', streamSimplify);

// Default to paste tab
selectTab('paste');



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
