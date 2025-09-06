const api = {
  base: '',
  keyEl: () => document.getElementById('apiKey'),
  taskEl: () => document.getElementById('task'),
  langEl: () => document.getElementById('language'),
  textEl: () => document.getElementById('textInput'),
  originalEl: () => document.getElementById('original'),
  plainEl: () => document.getElementById('plain'),
  risksEl: () => document.getElementById('risks'),
};

async function upload() {
  const file = document.getElementById('fileInput').files[0];
  if (!file) return alert('Select a file');
  const form = new FormData();
  form.append('file', file);
  const res = await fetch('/api/v1/upload', {
    method: 'POST',
    headers: { 'x-api-key': api.keyEl().value },
    body: form,
  });
  const data = await res.json();
  if (data.error) return alert(data.message || data.error);
  const text = (data.text) || (data.chunks?.map(c => c.text).join('\n') || '');
  api.textEl().value = text;
  api.originalEl().textContent = text;
}

async function runOnce() {
  const text = api.textEl().value;
  const res = await fetch('/api/v1/inference', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': api.keyEl().value,
    },
    body: JSON.stringify({ text, task: api.taskEl().value, language: api.langEl().value })
  });
  const data = await res.json();
  if (data.error) return alert(data.message || data.error);
  api.plainEl().textContent = data.plain_language || '';
  renderRisks(data.risks_detected || []);
}

async function streamRun() {
  const text = api.textEl().value;
  api.plainEl().textContent = '';
  const res = await fetch('/api/v1/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': api.keyEl().value,
    },
    body: JSON.stringify({ text, task: api.taskEl().value, language: api.langEl().value })
  });
  if (!res.body) return;
  const reader = res.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buf = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const parts = buf.split('\n\n');
    for (let i = 0; i < parts.length - 1; i++) {
      handleSSE(parts[i]);
    }
    buf = parts[parts.length - 1];
  }
}

function handleSSE(chunk) {
  const lines = chunk.split('\n');
  let event = 'message';
  let data = '';
  for (const l of lines) {
    if (l.startsWith('event:')) event = l.replace('event:', '').trim();
    if (l.startsWith('data:')) data += l.replace('data:', '').trim();
  }
  if (event === 'token') {
    api.plainEl().textContent += data;
  } else if (event === 'error') {
    console.error('Stream error:', data);
  }
}

function renderRisks(risks) {
  const ul = api.risksEl();
  ul.innerHTML = '';
  risks.forEach(r => {
    const li = document.createElement('li');
    li.className = `risk-item risk-${r.severity || 'medium'}`;
    li.innerHTML = `<strong>${r.type}</strong> - ${r.explanation} <em>(${r.severity})</em>`;
    li.title = r.clause_excerpt || '';
    li.addEventListener('click', () => {
      alert(`${r.type.toUpperCase()}\n\nExcerpt:\n${r.clause_excerpt}\n\nSuggested action:\n${r.suggested_action}`);
    });
    ul.appendChild(li);
  });
}

document.getElementById('uploadBtn').addEventListener('click', upload);

document.getElementById('runBtn').addEventListener('click', runOnce);

document.getElementById('streamBtn').addEventListener('click', streamRun);

document.getElementById('textInput').addEventListener('input', () => {
  api.originalEl().textContent = api.textEl().value;
});

document.getElementById('exportBtn').addEventListener('click', () => {
  const report = {
    original: api.originalEl().textContent,
    plain: api.plainEl().textContent,
    risks: Array.from(api.risksEl().querySelectorAll('li')).map(li => li.textContent)
  };
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'report.json'; a.click();
  URL.revokeObjectURL(url);
});
