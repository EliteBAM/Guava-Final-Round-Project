# Intake CRM: Overview

## What it is

A mock legal-intake CRM for law practices. It does two jobs:

- **Hosts the practice's PDF templates**, which the main app fetches through the API. Each template the main app uses is tagged with a *kind*, such as `fee_agreement`.
- **Shows PNC (Potential New Client) records** as the main app creates them, each with the call's full intake record, so you can see that the main app is working.

It runs on this PC only (`127.0.0.1`).

## Scope

Deliberately minimal: two tabs in the UI and four API endpoints. It does **not** have search, filtering, PNC editing, user accounts, or network deployment.

## Features

**Document Library**
- Drag PDFs onto the page, or click *browse files*, to add them. The details window opens straight away so you can name the document.
- Grid of documents with first-page thumbnails. Templates added by `npm run seed` show their kind under the name.
- Click a document to open its details window:
  - **Rename:** change the name and press **Done** (or Enter).
  - **Trash:** asks you to confirm before deleting.
  - **Close.**
  - The details also show the document's **kind**, or *Not set* for documents added by hand.
  - **Open PDF.**
- PDF only. Other file types are rejected with a message.

**PNC Records**
- A list on the left, newest first. Records created through the API carry an **API** badge.
- The selected record fills the page:
  - name, when it was received and last updated, how it was created, and the call's disposition;
  - the summary (the caller's account, in their own words);
  - **Flags for the attorney**, as chips;
  - **Intake record:** one card each for Caller, Incident, Injuries and treatment, Liability, Insurance, Parties, and Conflict check. A section with nothing in it shows a dashed *Not collected* card, as do all of them on a PNC added by hand;
  - **Missing information:** the fields the call didn't collect;
  - **Documents:** the signing packet, *Not sent yet* until the e-signature step is built.
- **New PNC** adds a record by hand.
- PNCs posted through the API slide into the list live, without a refresh. When the main app sends a call again, its PNC updates in place.

**Top bar:** the two tabs with their counts, and a **Live** dot that shows the page is connected for live updates.

## How to run

You need Node 22.13 or newer.

```
npm install
npm start
```

Then open <http://127.0.0.1:3000>.

To load the document templates from `../Assets` into the library, run `npm run seed` once. It's safe to run again: templates already in the library are skipped.

- The terminal prints the API key and logs every API call.
- Press `Ctrl+C` to stop the server.
- To use a different port, set the `PORT` environment variable before starting. In PowerShell: `$env:PORT = 4000; npm start`.
- To use a separate data folder, for example for a test run, set `DATA_DIR` the same way. `npm run seed` honours it too.
- An existing `data/intake.db` from before the record and kind columns is upgraded automatically when the server or the seed script opens it.

`.npmrc` stops npm from running install scripts and from downloading optional extra packages.

## Where data lives

| Path | Contents |
|---|---|
| `data/intake.db` | PNC and document records (SQLite) |
| `data/documents/` | The uploaded PDFs |
| `data/api-key.txt` | The API key |

Delete `data/` to reset everything. A new API key is created on the next start; run `npm run seed` again to restore the templates.

## Project layout

| Path | What it is |
|---|---|
| `server.js` | Web server, API, live updates (no framework) |
| `lib/db.js` | Database tables, the column upgrade, and queries (built-in `node:sqlite`) |
| `lib/paths.js` | Where the data lives (shared by the server and the seed script) |
| `seed.js` | Adds the `../Assets` templates to the library (`npm run seed`) |
| `public/` | The UI: plain HTML, CSS and JavaScript |
| `PRODUCT.md` / `DESIGN.md` | Product notes and the visual design system |
| `Documents/` | This documentation, and `Changelogs/` for changes made after the first version |

**Third-party code:**
- `pdfjs-dist` (Mozilla PDF.js, Apache-2.0) draws the thumbnails.
- `@fontsource-variable/manrope` (OFL-1.1) supplies the font.

API details: [2-API.md](2-API.md).
