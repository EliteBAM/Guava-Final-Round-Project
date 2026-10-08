import { DatabaseSync } from 'node:sqlite';
import { randomUUID } from 'node:crypto';

const SCHEMA = `
  CREATE TABLE IF NOT EXISTS pncs (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    summary    TEXT NOT NULL DEFAULT '',
    source     TEXT NOT NULL CHECK (source IN ('api', 'manual')),
    created_at TEXT NOT NULL,
    call_id    TEXT,
    record     TEXT,
    updated_at TEXT
  );
  CREATE TABLE IF NOT EXISTS documents (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    filename   TEXT NOT NULL,
    size       INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    kind       TEXT
  );
`;

// Columns added after the first release. Databases created before them get the columns on open.
const ADDED_COLUMNS = {
  pncs: { call_id: 'TEXT', record: 'TEXT', updated_at: 'TEXT' },
  documents: { kind: 'TEXT' },
};

// SQLite can't add a UNIQUE column, so uniqueness is an index (NULLs don't clash).
const INDEXES = `
  CREATE UNIQUE INDEX IF NOT EXISTS pncs_call_id ON pncs (call_id);
  CREATE UNIQUE INDEX IF NOT EXISTS documents_kind ON documents (kind);
`;

function migrate(db) {
  for (const [table, columns] of Object.entries(ADDED_COLUMNS)) {
    const have = new Set(db.prepare(`PRAGMA table_info(${table})`).all().map((c) => c.name));
    for (const [column, type] of Object.entries(columns)) {
      if (!have.has(column)) db.exec(`ALTER TABLE ${table} ADD COLUMN ${column} ${type}`);
    }
  }
}

function parseRecord(text) {
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

const toPnc = (row) => row && {
  id: row.id,
  name: row.name,
  summary: row.summary,
  source: row.source,
  createdAt: row.created_at,
  updatedAt: row.updated_at ?? row.created_at,
  callId: row.call_id ?? null,
  record: parseRecord(row.record),
};

const toDocument = (row) => row && {
  id: row.id,
  name: row.name,
  filename: row.filename,
  size: row.size,
  createdAt: row.created_at,
  kind: row.kind ?? null,
};

export function openDatabase(file) {
  const db = new DatabaseSync(file);
  db.exec('PRAGMA journal_mode = WAL;');
  db.exec(SCHEMA);
  migrate(db);
  db.exec(INDEXES);

  const q = {
    listPncs: db.prepare('SELECT * FROM pncs ORDER BY created_at DESC, rowid DESC'),
    getPnc: db.prepare('SELECT * FROM pncs WHERE id = ?'),
    getPncByCall: db.prepare('SELECT * FROM pncs WHERE call_id = ?'),
    insertPnc: db.prepare(
      'INSERT INTO pncs (id, name, summary, source, created_at, call_id, record, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
    ),
    updatePnc: db.prepare('UPDATE pncs SET name = ?, summary = ?, record = ?, updated_at = ? WHERE id = ?'),
    listDocs: db.prepare('SELECT * FROM documents ORDER BY created_at DESC, rowid DESC'),
    getDoc: db.prepare('SELECT * FROM documents WHERE id = ?'),
    getDocByKind: db.prepare('SELECT * FROM documents WHERE kind = ?'),
    insertDoc: db.prepare('INSERT INTO documents (id, name, filename, size, created_at, kind) VALUES (?, ?, ?, ?, ?, ?)'),
    renameDoc: db.prepare('UPDATE documents SET name = ? WHERE id = ?'),
    deleteDoc: db.prepare('DELETE FROM documents WHERE id = ?'),
  };

  return {
    listPncs: () => q.listPncs.all().map(toPnc),
    getPnc: (id) => toPnc(q.getPnc.get(id)),
    createPnc({ name, summary = '', source }) {
      const id = randomUUID();
      const now = new Date().toISOString();
      q.insertPnc.run(id, name, summary, source, now, null, null, now);
      return toPnc(q.getPnc.get(id));
    },
    // Create or update the PNC for a main-app call. Returns { pnc, created }.
    upsertPncByCall({ callId, name, summary = '', record = null }) {
      const now = new Date().toISOString();
      const json = record === null ? null : JSON.stringify(record);
      const existing = q.getPncByCall.get(callId);
      if (existing) {
        q.updatePnc.run(name, summary, json, now, existing.id);
        return { pnc: toPnc(q.getPnc.get(existing.id)), created: false };
      }
      const id = randomUUID();
      q.insertPnc.run(id, name, summary, 'api', now, callId, json, now);
      return { pnc: toPnc(q.getPnc.get(id)), created: true };
    },

    listDocuments: () => q.listDocs.all().map(toDocument),
    getDocument: (id) => toDocument(q.getDoc.get(id)),
    getDocumentByKind: (kind) => toDocument(q.getDocByKind.get(kind)),
    createDocument({ id = randomUUID(), name, filename, size, kind = null }) {
      q.insertDoc.run(id, name, filename, size, new Date().toISOString(), kind);
      return toDocument(q.getDoc.get(id));
    },
    renameDocument(id, name) {
      return q.renameDoc.run(name, id).changes > 0 ? toDocument(q.getDoc.get(id)) : null;
    },
    deleteDocument: (id) => q.deleteDoc.run(id).changes > 0,
  };
}
