// Adds the template PDFs from ../Assets to the Document Library, each tagged with a kind the main app looks up.
// Safe to run again: a kind that's already in the library is skipped. Run with `npm run seed`.

import fs from 'node:fs';
import path from 'node:path';
import { openDatabase } from './lib/db.js';
import { ROOT, DOCS_DIR, DB_FILE, docPath } from './lib/paths.js';

const ASSETS_DIR = process.env.ASSETS_DIR ? path.resolve(process.env.ASSETS_DIR) : path.resolve(ROOT, '..', 'Assets');

// Listed in the order they're signed; the library shows the first one first.
const TEMPLATES = [
  { kind: 'statement_of_client_rights', name: 'Statement of Client’s Rights', file: 'statement-of-client-rights.pdf' },
  { kind: 'fee_agreement', name: 'Contingency Fee Agreement', file: 'contingency-fee-agreement.pdf' },
  { kind: 'hipaa_authorization', name: 'HIPAA Authorization', file: 'hipaa-authorization.pdf' },
  { kind: 'client_questionnaire', name: 'Client Questionnaire', file: 'client-questionnaire.pdf' },
];

fs.mkdirSync(DOCS_DIR, { recursive: true });
const db = openDatabase(DB_FILE);

// newest first in the library, so add them last to first
for (const template of [...TEMPLATES].reverse()) {
  if (db.getDocumentByKind(template.kind)) {
    console.log(`skipped  ${template.name} (already in the library)`);
    continue;
  }
  const source = path.join(ASSETS_DIR, template.file);
  const body = fs.readFileSync(source);
  if (body.subarray(0, 5).toString('latin1') !== '%PDF-') throw new Error(`${source} is not a PDF.`);

  const doc = db.createDocument({ name: template.name, filename: template.file, size: body.length, kind: template.kind });
  fs.writeFileSync(docPath(doc.id), body);
  console.log(`added    ${template.name} (${template.kind})`);
}
