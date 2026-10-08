import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { openDatabase } from './lib/db.js';
import { ROOT, DATA_DIR, DOCS_DIR, DB_FILE, docPath } from './lib/paths.js';

const HOST = '127.0.0.1';
const PORT = Number(process.env.PORT) || 3000;
const PUBLIC_DIR = path.join(ROOT, 'public');
const KEY_FILE = path.join(DATA_DIR, 'api-key.txt');

const MAX_JSON_BYTES = 64 * 1024;
const MAX_PDF_BYTES = 50 * 1024 * 1024;
const MAX_NAME = 200;
const MAX_SUMMARY = 5000;
const CALL_ID = /^[A-Za-z0-9._:-]{1,200}$/;

fs.mkdirSync(DOCS_DIR, { recursive: true });
const db = openDatabase(DB_FILE);
const API_KEY = loadApiKey();

// Third-party browser files, served from node_modules by explicit allowlist only.
const VENDOR = {
  '/vendor/pdf.min.mjs': 'node_modules/pdfjs-dist/build/pdf.min.mjs',
  '/vendor/pdf.worker.min.mjs': 'node_modules/pdfjs-dist/build/pdf.worker.min.mjs',
  '/vendor/manrope.woff2': 'node_modules/@fontsource-variable/manrope/files/manrope-latin-wght-normal.woff2',
};

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2',
  '.ico': 'image/x-icon',
};

const ALLOWED_HOSTS = new Set([`127.0.0.1:${PORT}`, `localhost:${PORT}`]);

// ---------------------------------------------------------------- helpers

function loadApiKey() {
  try {
    const key = fs.readFileSync(KEY_FILE, 'utf8').trim();
    if (key) return key;
  } catch { /* first run */ }
  const key = crypto.randomBytes(24).toString('base64url');
  fs.writeFileSync(KEY_FILE, key + '\n', { mode: 0o600 });
  return key;
}

function keyMatches(given) {
  if (typeof given !== 'string') return false;
  const a = Buffer.from(given);
  const b = Buffer.from(API_KEY);
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

class HttpError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function sendJson(res, status, body) {
  const data = JSON.stringify(body);
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(data),
    'Cache-Control': 'no-store',
  });
  res.end(data);
}

function readBody(req, limit) {
  return new Promise((resolve, reject) => {
    const declared = Number(req.headers['content-length']);
    if (declared > limit) return reject(new HttpError(413, `Request body is larger than ${limit} bytes.`));
    const chunks = [];
    let size = 0;
    req.on('data', (chunk) => {
      size += chunk.length;
      if (size > limit) {
        reject(new HttpError(413, `Request body is larger than ${limit} bytes.`));
        req.destroy();
      } else {
        chunks.push(chunk);
      }
    });
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

async function readJson(req) {
  const type = req.headers['content-type'] || '';
  if (!type.toLowerCase().startsWith('application/json')) {
    throw new HttpError(415, 'Send the body as JSON with Content-Type: application/json.');
  }
  const raw = await readBody(req, MAX_JSON_BYTES);
  try {
    const value = JSON.parse(raw.toString('utf8'));
    if (value === null || typeof value !== 'object' || Array.isArray(value)) throw new Error();
    return value;
  } catch {
    throw new HttpError(400, 'The request body is not a valid JSON object.');
  }
}

function cleanText(value, field, { required = false, max }) {
  if (value === undefined || value === null) {
    if (required) throw new HttpError(400, `"${field}" is required.`);
    return '';
  }
  if (typeof value !== 'string') throw new HttpError(400, `"${field}" must be a string.`);
  const text = value.trim();
  if (required && !text) throw new HttpError(400, `"${field}" must not be empty.`);
  if (text.length > max) throw new HttpError(400, `"${field}" must be ${max} characters or fewer.`);
  return text;
}

function pncFromBody(body, source) {
  return {
    name: cleanText(body.name, 'name', { required: true, max: MAX_NAME }),
    summary: cleanText(body.summary, 'summary', { max: MAX_SUMMARY }),
    source,
  };
}

function recordFromBody(body) {
  const { record } = body;
  if (record === undefined || record === null) return null;
  if (typeof record !== 'object' || Array.isArray(record)) throw new HttpError(400, '"record" must be a JSON object.');
  return record;
}

function publicDocument(doc) {
  return { id: doc.id, name: doc.name, kind: doc.kind, size: doc.size, createdAt: doc.createdAt };
}

function sendPdf(res, doc, disposition) {
  const file = docPath(doc.id);
  let stat;
  try {
    stat = fs.statSync(file);
  } catch {
    throw new HttpError(404, 'The document file is missing.');
  }
  const filename = `${doc.name}.pdf`;
  const ascii = filename.replace(/[^\x20-\x7e]/g, '_').replace(/["\\]/g, '_');
  res.writeHead(200, {
    'Content-Type': 'application/pdf',
    'Content-Length': stat.size,
    'Content-Disposition': `${disposition}; filename="${ascii}"; filename*=UTF-8''${encodeURIComponent(filename)}`,
    'Cache-Control': 'no-store',
  });
  fs.createReadStream(file).pipe(res);
}

function serveFile(res, file) {
  fs.stat(file, (err, stat) => {
    if (err || !stat.isFile()) return sendJson(res, 404, { error: 'Not found.' });
    res.writeHead(200, {
      'Content-Type': MIME[path.extname(file)] || 'application/octet-stream',
      'Content-Length': stat.size,
      'Cache-Control': 'no-cache',
    });
    fs.createReadStream(file).pipe(res);
  });
}

// ---------------------------------------------------------------- live events

const listeners = new Set();

function broadcast(event, data) {
  const frame = `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
  for (const res of listeners) res.write(frame);
}

function openEventStream(req, res) {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream; charset=utf-8',
    'Cache-Control': 'no-store',
    Connection: 'keep-alive',
  });
  res.write('retry: 3000\n\n');
  listeners.add(res);
  const ping = setInterval(() => res.write(': ping\n\n'), 25000);
  req.on('close', () => {
    clearInterval(ping);
    listeners.delete(res);
  });
}

// ---------------------------------------------------------------- routes

async function handleApi(req, res, parts) {
  if (!keyMatches(req.headers['x-api-key'])) {
    throw new HttpError(401, 'Missing or invalid API key. Send it in the X-API-Key header.');
  }
  const [resource, id, extra] = parts;

  if (resource === 'pncs' && !id) {
    if (req.method !== 'POST') throw new HttpError(405, 'Use POST to create a PNC.');
    const pnc = db.createPnc(pncFromBody(await readJson(req), 'api'));
    broadcast('pnc-created', pnc);
    return sendJson(res, 201, pnc);
  }

  // Create or update by the main app's call ID, so sending the same call twice never makes a duplicate.
  if (resource === 'pncs' && id && !extra) {
    if (req.method !== 'PUT') throw new HttpError(405, 'Use PUT to create or update a PNC by call ID.');
    if (!CALL_ID.test(id)) throw new HttpError(400, 'The call ID must be 1 to 200 letters, digits, or . _ : - characters.');
    const body = await readJson(req);
    const { pnc, created } = db.upsertPncByCall({ callId: id, ...pncFromBody(body, 'api'), record: recordFromBody(body) });
    broadcast(created ? 'pnc-created' : 'pnc-updated', pnc);
    return sendJson(res, created ? 201 : 200, pnc);
  }

  if (resource === 'documents' && !extra) {
    if (req.method !== 'GET') throw new HttpError(405, 'Use GET to retrieve documents.');
    if (!id) return sendJson(res, 200, db.listDocuments().map(publicDocument));
    const doc = db.getDocument(id);
    if (!doc) throw new HttpError(404, `No document with id "${id}".`);
    return sendPdf(res, doc, 'attachment');
  }

  throw new HttpError(404, 'Unknown API route.');
}

async function handleApp(req, res, parts) {
  // Browser-only routes. Reject cross-site writes as a CSRF guard.
  const origin = req.headers.origin;
  if (req.method !== 'GET' && origin && !ALLOWED_HOSTS.has(origin.replace(/^https?:\/\//, ''))) {
    throw new HttpError(403, 'Cross-origin requests are not allowed.');
  }
  const [resource, id, extra] = parts;

  if (resource === 'events' && !id && req.method === 'GET') return openEventStream(req, res);

  if (resource === 'pncs' && !id) {
    if (req.method === 'GET') return sendJson(res, 200, db.listPncs());
    if (req.method === 'POST') {
      const pnc = db.createPnc(pncFromBody(await readJson(req), 'manual'));
      broadcast('pnc-created', pnc);
      return sendJson(res, 201, pnc);
    }
    throw new HttpError(405, 'Method not allowed.');
  }

  if (resource === 'documents' && !id) {
    if (req.method === 'GET') return sendJson(res, 200, db.listDocuments());
    if (req.method === 'POST') return uploadDocument(req, res);
    throw new HttpError(405, 'Method not allowed.');
  }

  if (resource === 'documents' && id) {
    const doc = db.getDocument(id);
    if (!doc) throw new HttpError(404, `No document with id "${id}".`);

    if (extra === 'file' && req.method === 'GET') return sendPdf(res, doc, 'inline');
    if (extra) throw new HttpError(404, 'Not found.');

    if (req.method === 'PATCH') {
      const name = cleanText((await readJson(req)).name, 'name', { required: true, max: MAX_NAME });
      return sendJson(res, 200, db.renameDocument(id, name));
    }
    if (req.method === 'DELETE') {
      db.deleteDocument(id);
      fs.rm(docPath(id), { force: true }, () => {});
      res.writeHead(204);
      return res.end();
    }
    throw new HttpError(405, 'Method not allowed.');
  }

  throw new HttpError(404, 'Not found.');
}

async function uploadDocument(req, res) {
  let filename;
  try {
    filename = decodeURIComponent(req.headers['x-filename'] || '').trim();
  } catch {
    throw new HttpError(400, 'The X-Filename header is not valid.');
  }
  if (!filename) throw new HttpError(400, 'Send the original file name in the X-Filename header.');

  const body = await readBody(req, MAX_PDF_BYTES);
  if (body.length < 5 || body.subarray(0, 5).toString('latin1') !== '%PDF-') {
    throw new HttpError(415, `"${filename}" is not a PDF. Only PDF templates can be added.`);
  }

  const id = crypto.randomUUID();
  const name = (filename.replace(/\.pdf$/i, '').trim() || 'Untitled').slice(0, MAX_NAME);
  fs.writeFileSync(docPath(id), body);
  const doc = db.createDocument({ id, name, filename, size: body.length });
  return sendJson(res, 201, doc);
}

// ---------------------------------------------------------------- server

const server = http.createServer(async (req, res) => {
  const started = Date.now();
  try {
    if (!ALLOWED_HOSTS.has(req.headers.host || '')) throw new HttpError(421, 'Unexpected Host header.');

    const url = new URL(req.url, `http://${req.headers.host}`);
    const parts = url.pathname.split('/').filter(Boolean).map(decodeURIComponent);

    if (parts[0] === 'api' && parts[1] === 'v1') {
      res.on('finish', () => {
        console.log(`${new Date().toISOString()}  API ${req.method} ${url.pathname} -> ${res.statusCode} (${Date.now() - started} ms)`);
      });
      return await handleApi(req, res, parts.slice(2));
    }
    if (parts[0] === 'app') return await handleApp(req, res, parts.slice(1));

    if (req.method !== 'GET' && req.method !== 'HEAD') throw new HttpError(405, 'Method not allowed.');
    if (VENDOR[url.pathname]) return serveFile(res, path.join(ROOT, VENDOR[url.pathname]));

    const relative = url.pathname === '/' ? 'index.html' : url.pathname.slice(1);
    const file = path.resolve(PUBLIC_DIR, relative);
    if (!file.startsWith(PUBLIC_DIR + path.sep)) throw new HttpError(404, 'Not found.');
    return serveFile(res, file);
  } catch (err) {
    if (res.headersSent) return res.destroy();
    if (err instanceof HttpError) return sendJson(res, err.status, { error: err.message });
    if (err instanceof URIError) return sendJson(res, 400, { error: 'The URL is not valid.' });
    console.error(err);
    return sendJson(res, 500, { error: 'Something went wrong on the server.' });
  }
});

server.listen(PORT, HOST, () => {
  console.log(`Intake CRM running at http://${HOST}:${PORT}`);
  console.log(`API key (also in data/api-key.txt): ${API_KEY}`);
});
