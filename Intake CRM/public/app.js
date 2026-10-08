// Intake CRM front end: two tabs (Document Library, PNC Records), no framework.

const $ = (sel, root = document) => root.querySelector(sel);

const state = {
  docs: [],
  pncs: [],
  selectedPncId: null,
  creatingPnc: false,
  dialogDocId: null,
  dialogQueue: [],
  newDocIds: new Set(),
};

// ---------------------------------------------------------------- formatting

const dateTime = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' });
const timeOnly = new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' });
const dayMonth = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short' });
const dateOnly = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' });

function shortWhen(iso) {
  const d = new Date(iso);
  const now = new Date();
  return d.toDateString() === now.toDateString() ? timeOnly.format(d) : dayMonth.format(d);
}

function fileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key === 'class') node.className = value;
    else if (key === 'text') node.textContent = value;
    else node.setAttribute(key, value);
  }
  node.append(...children.filter(Boolean));
  return node;
}

function icon(name, extraClass = '') {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('class', `icon ${extraClass}`.trim());
  svg.setAttribute('aria-hidden', 'true');
  const use = document.createElementNS(ns, 'use');
  use.setAttribute('href', `#i-${name}`);
  svg.append(use);
  return svg;
}

// ---------------------------------------------------------------- server calls

async function request(method, url, { json, body, headers = {} } = {}) {
  const init = { method, headers: { ...headers } };
  if (json !== undefined) {
    init.headers['Content-Type'] = 'application/json';
    init.body = JSON.stringify(json);
  } else if (body !== undefined) {
    init.body = body;
  }
  const res = await fetch(url, init);
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(data?.error || `The server answered ${res.status}.`);
  return data;
}

// ---------------------------------------------------------------- tabs

const tabs = [...document.querySelectorAll('[role="tab"]')];

function showTab(name, { focus = false } = {}) {
  if (!tabs.some((t) => t.dataset.tab === name)) name = 'library';
  for (const tab of tabs) {
    const selected = tab.dataset.tab === name;
    tab.setAttribute('aria-selected', String(selected));
    tab.tabIndex = selected ? 0 : -1;
    $(`#${tab.getAttribute('aria-controls')}`).hidden = !selected;
    if (selected && focus) tab.focus();
  }
  if (location.hash !== `#${name}`) history.replaceState(null, '', `#${name}`);
}

for (const tab of tabs) {
  tab.addEventListener('click', () => showTab(tab.dataset.tab));
  tab.addEventListener('keydown', (e) => {
    const i = tabs.indexOf(tab);
    const next = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: tabs.length - 1 }[e.key];
    if (next === undefined) return;
    e.preventDefault();
    showTab(tabs[(next + tabs.length) % tabs.length].dataset.tab, { focus: true });
  });
}

window.addEventListener('hashchange', () => showTab(location.hash.slice(1)));

function updateCounts() {
  $('#count-library').textContent = state.docs.length || '';
  $('#count-pncs').textContent = state.pncs.length || '';
}

// ---------------------------------------------------------------- PDF thumbnails

let pdfjsPromise;
function loadPdfjs() {
  pdfjsPromise ??= import('/vendor/pdf.min.mjs').then((lib) => {
    lib.GlobalWorkerOptions.workerSrc = '/vendor/pdf.worker.min.mjs';
    return lib;
  });
  return pdfjsPromise;
}

const thumbCache = new Map(); // `${id}:${width}` -> Promise<canvas>

function renderThumb(docId, cssWidth) {
  const key = `${docId}:${cssWidth}`;
  if (!thumbCache.has(key)) {
    const job = (async () => {
      const pdfjs = await loadPdfjs();
      const pdf = await pdfjs.getDocument({ url: `/app/documents/${docId}/file` }).promise;
      try {
        const page = await pdf.getPage(1);
        const base = page.getViewport({ scale: 1 });
        const scale = (cssWidth * Math.min(window.devicePixelRatio || 1, 2.5)) / base.width;
        const viewport = page.getViewport({ scale });
        const canvas = document.createElement('canvas');
        canvas.width = Math.floor(viewport.width);
        canvas.height = Math.floor(viewport.height);
        await page.render({ canvas, viewport }).promise;
        return canvas;
      } finally {
        pdf.destroy();
      }
    })();
    job.catch(() => thumbCache.delete(key));
    thumbCache.set(key, job);
  }
  return thumbCache.get(key);
}

function fillPage(pageEl, docId, cssWidth) {
  pageEl.replaceChildren(el('span', { class: 'page-skeleton', 'aria-hidden': 'true' }));
  renderThumb(docId, cssWidth)
    .then((source) => {
      // A canvas can only live in one place; copy it for each slot that shows it.
      const canvas = document.createElement('canvas');
      canvas.width = source.width;
      canvas.height = source.height;
      canvas.getContext('2d').drawImage(source, 0, 0);
      canvas.setAttribute('aria-hidden', 'true');
      pageEl.replaceChildren(canvas);
    })
    .catch(() => {
      pageEl.replaceChildren(el('span', { class: 'page-fallback', text: 'Preview unavailable' }));
    });
}

// ---------------------------------------------------------------- document library

const grid = $('#doc-grid');
const docTemplate = $('#tpl-doc');

function renderDocs() {
  const items = state.docs.map((doc) => {
    const li = docTemplate.content.firstElementChild.cloneNode(true);
    const button = $('.doc', li);
    button.dataset.id = doc.id;
    button.setAttribute('aria-label', `${doc.name}, PDF, ${fileSize(doc.size)}. Open details`);
    $('.doc-name', li).textContent = doc.name;
    $('.doc-kind', li).textContent = doc.kind || '';
    if (doc.kind) $('.doc-kind', li).title = `Kind: ${doc.kind}`;
    $('.doc-meta', li).textContent = `${fileSize(doc.size)} · ${shortWhen(doc.createdAt)}`;
    if (state.newDocIds.has(doc.id)) button.classList.add('is-new');
    fillPage($('.page', li), doc.id, 200);
    return li;
  });
  state.newDocIds.clear();
  grid.replaceChildren(...items);
  $('#library-empty').hidden = state.docs.length > 0;
  grid.hidden = state.docs.length === 0;
  updateCounts();
}

grid.addEventListener('click', (e) => {
  const button = e.target.closest('.doc');
  if (button) openDocDialog(button.dataset.id);
});

let noticeTimer;
function showNotice(message) {
  const notice = $('#library-notice');
  notice.textContent = message;
  notice.hidden = false;
  clearTimeout(noticeTimer);
  noticeTimer = setTimeout(() => { notice.hidden = true; }, 7000);
}

function isPdf(file) {
  return file.type === 'application/pdf' || /\.pdf$/i.test(file.name);
}

async function addFiles(fileList) {
  const files = [...fileList];
  const rejected = files.filter((f) => !isPdf(f));
  if (rejected.length) {
    const names = rejected.map((f) => `“${f.name}”`).join(', ');
    showNotice(`${names} ${rejected.length === 1 ? "isn't a PDF" : "aren't PDFs"}. Only PDF templates can be added.`);
  }

  const added = [];
  for (const file of files.filter(isPdf)) {
    try {
      const doc = await request('POST', '/app/documents', {
        body: file,
        headers: { 'Content-Type': 'application/pdf', 'X-Filename': encodeURIComponent(file.name) },
      });
      added.push(doc);
    } catch (err) {
      showNotice(err.message);
    }
  }
  if (!added.length) return;

  for (const doc of added) state.newDocIds.add(doc.id);
  state.docs = [...[...added].reverse(), ...state.docs]; // newest first, like the server
  renderDocs();

  // Each new document opens its details so it can be named; several queue up in drop order.
  state.dialogQueue.push(...added.map((d) => d.id));
  if (!dialog.open) openNextQueued();
}

const fileInput = $('#file-input');
document.addEventListener('click', (e) => {
  if (e.target.closest('[data-action="browse"]')) fileInput.click();
});
fileInput.addEventListener('change', () => {
  addFiles(fileInput.files);
  fileInput.value = '';
});

// Drag and drop: anywhere on the page while the library is showing.
const overlay = $('#drop-overlay');
let dragDepth = 0;

const libraryVisible = () => !$('#panel-library').hidden;
const carriesFiles = (e) => [...(e.dataTransfer?.types || [])].includes('Files');

window.addEventListener('dragenter', (e) => {
  if (!carriesFiles(e)) return;
  e.preventDefault();
  dragDepth++;
  if (libraryVisible() && !dialog.open) overlay.classList.add('is-active');
});
window.addEventListener('dragover', (e) => {
  if (!carriesFiles(e)) return;
  e.preventDefault();
  e.dataTransfer.dropEffect = libraryVisible() && !dialog.open ? 'copy' : 'none';
});
window.addEventListener('dragleave', (e) => {
  if (!carriesFiles(e)) return;
  dragDepth = Math.max(0, dragDepth - 1);
  if (dragDepth === 0) overlay.classList.remove('is-active');
});
window.addEventListener('drop', (e) => {
  if (!carriesFiles(e)) return;
  e.preventDefault();
  dragDepth = 0;
  overlay.classList.remove('is-active');
  if (libraryVisible() && !dialog.open) addFiles(e.dataTransfer.files);
});

// ---------------------------------------------------------------- document dialog

const dialog = $('#doc-dialog');
const docForm = $('#doc-form');
const nameInput = $('#doc-name');
const nameError = $('#doc-name-error');

function setNameError(message) {
  nameError.textContent = message || '';
  nameError.hidden = !message;
  nameInput.setAttribute('aria-invalid', String(Boolean(message)));
}

function showConfirm(show) {
  $('#doc-actions').hidden = show;
  $('#doc-confirm').hidden = !show;
  if (show) $('[data-action="confirm-trash"]').focus();
}

function openDocDialog(id) {
  const doc = state.docs.find((d) => d.id === id);
  if (!doc) return;
  state.dialogDocId = id;
  nameInput.value = doc.name;
  setNameError('');
  showConfirm(false);
  $('#doc-kind').textContent = doc.kind || 'Not set';
  $('#doc-added').textContent = dateTime.format(new Date(doc.createdAt));
  $('#doc-size').textContent = fileSize(doc.size);
  $('#doc-filename').textContent = doc.filename;
  $('#doc-id').textContent = doc.id;
  $('#doc-open').href = `/app/documents/${doc.id}/file`;
  fillPage($('#doc-preview'), doc.id, 220);
  dialog.showModal();
  nameInput.focus();
  nameInput.select();
}

function openNextQueued() {
  while (state.dialogQueue.length) {
    const id = state.dialogQueue.shift();
    if (state.docs.some((d) => d.id === id)) return openDocDialog(id);
  }
}

function closeDialog() {
  dialog.close();
}

dialog.addEventListener('close', () => {
  state.dialogDocId = null;
  setTimeout(openNextQueued, 120);
});

// Clicking the backdrop closes the dialog.
dialog.addEventListener('click', (e) => {
  if (e.target === dialog) closeDialog();
});

dialog.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && !$('#doc-confirm').hidden) {
    e.preventDefault();
    showConfirm(false);
  }
});

docForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const doc = state.docs.find((d) => d.id === state.dialogDocId);
  if (!doc) return closeDialog();

  const name = nameInput.value.trim();
  if (!name) {
    setNameError('Give the document a name.');
    nameInput.focus();
    return;
  }
  if (name === doc.name) return closeDialog();

  const save = $('#doc-save');
  save.setAttribute('aria-busy', 'true');
  try {
    const updated = await request('PATCH', `/app/documents/${doc.id}`, { json: { name } });
    Object.assign(doc, updated);
    renderDocs();
    closeDialog();
  } catch (err) {
    setNameError(err.message);
  } finally {
    save.removeAttribute('aria-busy');
  }
});

nameInput.addEventListener('input', () => setNameError(''));

dialog.addEventListener('click', async (e) => {
  const action = e.target.closest('[data-action]')?.dataset.action;
  if (action === 'close-dialog') closeDialog();
  if (action === 'trash') showConfirm(true);
  if (action === 'cancel-trash') {
    showConfirm(false);
    $('[data-action="trash"]').focus();
  }
  if (action === 'confirm-trash') {
    const id = state.dialogDocId;
    const button = e.target.closest('button');
    button.setAttribute('aria-busy', 'true');
    try {
      await request('DELETE', `/app/documents/${id}`);
      state.docs = state.docs.filter((d) => d.id !== id);
      for (const key of thumbCache.keys()) if (key.startsWith(`${id}:`)) thumbCache.delete(key);
      renderDocs();
      closeDialog();
    } catch (err) {
      showConfirm(false);
      setNameError(err.message);
    } finally {
      button.removeAttribute('aria-busy');
    }
  }
});

// ---------------------------------------------------------------- PNC records

const pncList = $('#pnc-list');
const pncTemplate = $('#tpl-pnc-item');
const detail = $('#pnc-detail');

function pncItem(pnc) {
  const li = pncTemplate.content.firstElementChild.cloneNode(true);
  const button = $('.pnc-item', li);
  button.dataset.id = pnc.id;
  $('.pnc-item-name', li).textContent = pnc.name;
  const time = $('.pnc-item-time', li);
  time.dateTime = pnc.createdAt;
  time.textContent = shortWhen(pnc.createdAt);
  time.title = dateTime.format(new Date(pnc.createdAt));
  $('.badge', li).hidden = pnc.source !== 'api';
  return li;
}

function renderPncList() {
  pncList.replaceChildren(...state.pncs.map(pncItem));
  $('#pnc-list-empty').hidden = state.pncs.length > 0;
  markSelected();
  updateCounts();
}

function markSelected() {
  for (const button of pncList.querySelectorAll('.pnc-item')) {
    const current = !state.creatingPnc && button.dataset.id === state.selectedPncId;
    if (current) button.setAttribute('aria-current', 'true');
    else button.removeAttribute('aria-current');
  }
}

function swapDetail(...nodes) {
  detail.classList.remove('is-swapping');
  detail.replaceChildren(...nodes);
  void detail.offsetWidth; // restart the entrance animation
  detail.classList.add('is-swapping');
  detail.scrollTop = 0;
}

// ---------------------------------------------------------------- PNC intake record

// The record the main app sends (intake.build_record in the agent): sections of field -> value.
const RECORD_SECTIONS = [
  ['caller', 'Caller'],
  ['incident', 'Incident'],
  ['injuries', 'Injuries and treatment'],
  ['liability', 'Liability'],
  ['coverage', 'Insurance'],
  ['parties', 'Parties'],
  ['conflicts', 'Conflict check'],
];
const FIRST_FIELDS = ['date', 'incident_type', 'status'];
const HIDDEN_FIELDS = new Set(['narrative']); // shown as the summary

const FIELD_LABELS = {
  date: 'Date of incident',
  incident_state: 'State',
  incident_location: 'Location',
  first_treatment_date: 'First treated',
  government_involved: 'Government involved',
  other_vehicle: 'Other vehicle',
  other_insurer: 'Other driver’s insurer',
  own_insurer: 'Their auto insurer',
  insurer_contact: 'Insurer contact',
  represented: 'Already has a lawyer',
  recording_consent: 'Recording consent',
  adverse: 'Named at screening',
  other_parties: 'Named in the story',
  status: 'Result',
  names_checked: 'Names checked',
  recheck: 'Re-check',
};
const VALUE_LABELS = {
  agree_to_recording: 'Yes',
  gave_statement: 'Gave a statement',
  new_injury_matter: 'New injury matter',
  not_needed: 'Not needed',
  pending_signature: 'Pending signature',
};
const ACRONYMS = { er: 'ER', um: 'UM', pip: 'PIP', sol: 'SOL' };

const FLAG_LABELS = {
  sol_urgent: 'Limitation deadline within 90 days',
  sol_expired_likely: 'Limitation period likely expired',
  sol_boundary_case: 'Limitation boundary case',
  pip_14_day_risk: 'PIP 14-day treatment risk',
  no_treatment: 'No treatment yet',
  route_nurse_intake: 'Route to nurse intake',
  non_mva_case_type: 'Not a motor vehicle case',
  government_defendant: 'Government defendant',
  out_of_state: 'Out of state',
  commercial_vehicle: 'Commercial vehicle',
  rideshare: 'Rideshare',
  hit_and_run: 'Hit and run',
  on_the_job: 'On the job (workers’ comp)',
  statement_given: 'Gave the insurer a statement',
  prior_similar_injury: 'Prior similar injury',
  no_seat_belt: 'No seat belt',
  recording_consent: 'Agreed to recording',
  fee_questions: 'Asked about fees',
  adverse_unknown: 'Other party unknown at screening',
  recheck_failed: 'Conflict re-check failed',
  disclosure_unverified: 'Disclosures not verified',
  next_steps_unverified: 'Next-steps line not verified',
  represented: 'Already represented',
};

function humanize(key) {
  const text = key.split('_').map((word) => ACRONYMS[word] ?? word).join(' ');
  return text.charAt(0).toUpperCase() + text.slice(1);
}

const fieldLabel = (key) => FIELD_LABELS[key] ?? humanize(key);

// Field values are the agent's choice keys (snake_case), ISO dates, or the caller's own words.
function displayValue(value) {
  if (value === null || value === undefined || value === '') return null;
  if (Array.isArray(value)) return value.length ? value.map(displayValue).filter(Boolean).join(', ') : null;
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value !== 'string') return String(value);
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return dateOnly.format(new Date(`${value}T00:00:00`));
  if (VALUE_LABELS[value]) return VALUE_LABELS[value];
  return /^[a-z0-9]+(_[a-z0-9]+)*$/.test(value) ? humanize(value) : value;
}

function sortedEntries(section) {
  const rank = (key) => (FIRST_FIELDS.includes(key) ? FIRST_FIELDS.indexOf(key) : FIRST_FIELDS.length);
  return Object.entries(section || {})
    .filter(([key]) => !HIDDEN_FIELDS.has(key))
    .sort(([a], [b]) => rank(a) - rank(b));
}

function emptyCard(title, text) {
  return el('div', { class: 'record-card is-empty' },
    el('h4', { text: title }),
    el('p', { class: 'record-empty', text }),
  );
}

function factCard(title, section) {
  const rows = sortedEntries(section)
    .map(([key, value]) => [fieldLabel(key), displayValue(value)])
    .filter(([, value]) => value !== null);
  if (!rows.length) return emptyCard(title, 'Not collected');
  return el('div', { class: 'record-card' },
    el('h4', { text: title }),
    el('dl', { class: 'record-facts' },
      ...rows.map(([label, value]) => el('div', {}, el('dt', { text: label }), el('dd', { text: value }))),
    ),
  );
}

// The signing packet's status, set by the main app (PATCH /pncs/{callId}/documents).
const DOCUMENT_STATUS = {
  sent: 'Waiting for the client to sign',
  client_signed: 'Signed by the client. Attorney countersignature requested by email.',
};

function documentsCard(docs) {
  if (!docs) return emptyCard('Signing packet', 'Not sent yet');
  const when = (iso) => (iso ? dateTime.format(new Date(iso)) : null);
  const sentTo = docs.sentVia === 'email' ? `By email to ${docs.sentTo}` : `By text to •••• ${docs.sentTo}`;
  const rows = [
    ['Status', DOCUMENT_STATUS[docs.status] ?? displayValue(docs.status)],
    ['Sent', docs.sentTo ? `${sentTo}${docs.sentAt ? `, ${when(docs.sentAt)}` : ''}` : when(docs.sentAt)],
    ['Client signed', when(docs.signedAt)],
    ['Documents', docs.items?.length ? docs.items.join(', ') : null],
    ['Envelope', docs.envelopeId || null],
  ].filter(([, value]) => value);
  return el('div', { class: 'record-card' },
    el('h4', { text: 'Signing packet' }),
    el('dl', { class: 'record-facts' },
      ...rows.map(([label, value]) => el('div', {}, el('dt', { text: label }), el('dd', { text: value }))),
    ),
  );
}

function recordSection(id, title, ...children) {
  return el('section', { class: 'pnc-section', 'aria-labelledby': `${id}-h` }, el('h3', { id: `${id}-h`, text: title }), ...children);
}

function flagsSection(record) {
  const flags = record?.flags || [];
  return recordSection('flags', 'Flags for the attorney',
    flags.length
      ? el('ul', { class: 'chips' }, ...flags.map((flag) => el('li', { class: 'chip', text: FLAG_LABELS[flag] ?? humanize(flag) })))
      : el('p', { class: 'record-note', text: record ? 'No flags.' : 'Not collected' }),
  );
}

function missingSection(record) {
  const missing = record?.completeness;
  if (!missing) return recordSection('missing', 'Missing information', el('p', { class: 'record-note', text: 'Not collected' }));
  const rows = [['Critical', missing.critical_missing], ['Important', missing.important_missing]]
    .filter(([, keys]) => keys?.length)
    .map(([label, keys]) => el('div', {}, el('dt', { text: label }), el('dd', { text: keys.map(fieldLabel).join(', ') })));
  return recordSection('missing', 'Missing information',
    rows.length ? el('dl', { class: 'record-facts missing' }, ...rows) : el('p', { class: 'record-note', text: 'Nothing missing.' }),
  );
}

function renderDetail() {
  if (state.creatingPnc) return renderPncForm();

  const pnc = state.pncs.find((p) => p.id === state.selectedPncId);
  if (!pnc) {
    swapDetail(
      el('div', { class: 'detail-empty' },
        icon('person', 'icon-lg'),
        el('p', { class: 'empty-title', text: state.pncs.length ? 'Select a PNC' : 'No PNCs yet' }),
        el('p', {
          text: state.pncs.length
            ? 'Choose a record on the left to see its details.'
            : 'Records appear here as soon as the main app sends them. You can also add one by hand.',
        }),
        state.pncs.length ? null : newPncButton(),
      ),
    );
    return;
  }

  const record = pnc.record;
  const created = new Date(pnc.createdAt);
  const updated = new Date(pnc.updatedAt);
  const wasUpdated = updated - created > 1000;
  const header = el('header', { class: 'pnc-header' },
    el('h1', { class: 'pnc-name', text: pnc.name }),
    el('p', { class: 'pnc-meta' },
      el('time', { datetime: pnc.createdAt, text: `Received ${dateTime.format(created)}` }),
      wasUpdated ? el('span', { class: 'sep', 'aria-hidden': 'true' }) : null,
      wasUpdated ? el('time', { datetime: pnc.updatedAt, text: `Updated ${dateTime.format(updated)}` }) : null,
      el('span', { class: 'sep', 'aria-hidden': 'true' }),
      el('span', { text: pnc.source === 'api' ? 'Created by the main app (API)' : 'Added by hand' }),
    ),
    record?.disposition
      ? el('p', { class: 'pnc-disposition' }, 'Disposition: ', el('strong', { text: displayValue(record.disposition) }))
      : null,
  );

  const summary = recordSection('summary', 'Summary',
    el('p', {
      class: pnc.summary ? 'pnc-summary' : 'pnc-summary is-empty',
      text: pnc.summary || 'No summary was provided.',
    }),
  );

  const intake = recordSection('intake', 'Intake record',
    el('div', { class: 'record-grid' }, ...RECORD_SECTIONS.map(([key, title]) => factCard(title, record?.[key]))),
  );

  const documents = recordSection('documents', 'Documents', documentsCard(pnc.documents));

  swapDetail(el('article', {}, header, summary, flagsSection(record), intake, missingSection(record), documents));
}

function newPncButton() {
  const button = el('button', { class: 'btn btn-primary', type: 'button' }, icon('plus'), 'New PNC');
  button.addEventListener('click', startNewPnc);
  return button;
}

function renderPncForm() {
  const nameField = el('input', {
    class: 'input', id: 'pnc-name', name: 'name', type: 'text', maxlength: '200', autocomplete: 'off', required: '',
  });
  const nameErr = el('span', { class: 'field-error', id: 'pnc-name-error' });
  nameErr.hidden = true;
  nameField.setAttribute('aria-describedby', 'pnc-name-error');
  const summaryField = el('textarea', { class: 'input', id: 'pnc-summary', name: 'summary', maxlength: '5000', rows: '6' });
  const formError = el('p', { class: 'form-error', role: 'alert' });
  formError.hidden = true;

  const submit = el('button', { class: 'btn btn-primary', type: 'submit' }, 'Create PNC');
  const cancel = el('button', { class: 'btn', type: 'button' }, 'Cancel');

  const form = el('form', { class: 'pnc-form', novalidate: '' },
    el('div', { class: 'pnc-form-head' },
      el('h1', { class: 'pnc-name', text: 'New PNC' }),
      el('p', { text: 'Add a potential new client by hand. The main app creates them through the API.' }),
    ),
    el('label', { class: 'field' }, el('span', { class: 'field-label', text: 'Name' }), nameField, nameErr),
    el('label', { class: 'field' },
      el('span', { class: 'field-label' }, 'Summary ', el('span', { class: 'optional', text: '(optional)' })),
      summaryField,
    ),
    formError,
    el('div', { class: 'form-actions' }, submit, cancel),
  );

  nameField.addEventListener('input', () => {
    nameErr.hidden = true;
    nameField.removeAttribute('aria-invalid');
  });

  cancel.addEventListener('click', () => {
    state.creatingPnc = false;
    markSelected();
    renderDetail();
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = nameField.value.trim();
    if (!name) {
      nameErr.textContent = 'Enter the client’s name.';
      nameErr.hidden = false;
      nameField.setAttribute('aria-invalid', 'true');
      nameField.focus();
      return;
    }
    submit.setAttribute('aria-busy', 'true');
    submit.disabled = true;
    try {
      const pnc = await request('POST', '/app/pncs', { json: { name, summary: summaryField.value } });
      addPnc(pnc, { select: true });
    } catch (err) {
      formError.textContent = err.message;
      formError.hidden = false;
      submit.disabled = false;
      submit.removeAttribute('aria-busy');
    }
  });

  swapDetail(form);
  nameField.focus();
}

function startNewPnc() {
  state.creatingPnc = true;
  markSelected();
  renderDetail();
}

$('#new-pnc').addEventListener('click', startNewPnc);

pncList.addEventListener('click', (e) => {
  const button = e.target.closest('.pnc-item');
  if (!button) return;
  state.creatingPnc = false;
  state.selectedPncId = button.dataset.id;
  markSelected();
  renderDetail();
});

// Up/down arrows move through the list.
pncList.addEventListener('keydown', (e) => {
  if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
  const buttons = [...pncList.querySelectorAll('.pnc-item')];
  const i = buttons.indexOf(document.activeElement);
  if (i === -1) return;
  e.preventDefault();
  const next = buttons[Math.min(buttons.length - 1, Math.max(0, i + (e.key === 'ArrowDown' ? 1 : -1)))];
  next.focus();
  next.click();
});

function updatePnc(pnc) {
  const index = state.pncs.findIndex((p) => p.id === pnc.id);
  if (index === -1) return addPnc(pnc);
  state.pncs[index] = pnc;
  const button = pncList.querySelector(`.pnc-item[data-id="${CSS.escape(pnc.id)}"]`);
  if (button) $('.pnc-item-name', button).textContent = pnc.name;
  if (!state.creatingPnc && state.selectedPncId === pnc.id) renderDetail();
}

function addPnc(pnc, { select = false } = {}) {
  if (state.pncs.some((p) => p.id === pnc.id)) {
    if (select) {
      state.creatingPnc = false;
      state.selectedPncId = pnc.id;
      markSelected();
      renderDetail();
    }
    return;
  }
  state.pncs.unshift(pnc);

  const li = pncItem(pnc);
  $('.pnc-item', li).classList.add('is-new');
  pncList.prepend(li);
  $('#pnc-list-empty').hidden = true;
  updateCounts();

  if (select || (!state.selectedPncId && !state.creatingPnc)) {
    state.creatingPnc = false;
    state.selectedPncId = pnc.id;
    renderDetail();
  } else if (!state.creatingPnc && !state.pncs.find((p) => p.id === state.selectedPncId)) {
    renderDetail();
  }
  markSelected();
}

// ---------------------------------------------------------------- live updates

function connectEvents() {
  const live = $('#live');
  const label = $('.live-label', live);
  const set = (s, text) => { live.dataset.state = s; label.textContent = text; };

  const source = new EventSource('/app/events');
  source.addEventListener('open', () => set('open', 'Live'));
  source.addEventListener('error', () => set(source.readyState === EventSource.CLOSED ? 'closed' : 'connecting', 'Reconnecting'));
  source.addEventListener('pnc-created', (e) => addPnc(JSON.parse(e.data)));
  source.addEventListener('pnc-updated', (e) => updatePnc(JSON.parse(e.data)));
}

// ---------------------------------------------------------------- start

async function start() {
  showTab(location.hash.slice(1) || 'library');
  try {
    [state.docs, state.pncs] = await Promise.all([request('GET', '/app/documents'), request('GET', '/app/pncs')]);
  } catch (err) {
    showNotice(`Couldn't load data: ${err.message}`);
  }
  state.selectedPncId = state.pncs[0]?.id ?? null;
  renderDocs();
  renderPncList();
  renderDetail();
  connectEvents();
}

start();
