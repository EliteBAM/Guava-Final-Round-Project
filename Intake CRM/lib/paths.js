import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

// DATA_DIR lets a test run use its own database and files instead of the real ones.
export const DATA_DIR = process.env.DATA_DIR ? path.resolve(process.env.DATA_DIR) : path.join(ROOT, 'data');
export const DOCS_DIR = path.join(DATA_DIR, 'documents');
export const DB_FILE = path.join(DATA_DIR, 'intake.db');

export const docPath = (id) => path.join(DOCS_DIR, `${id}.pdf`);
