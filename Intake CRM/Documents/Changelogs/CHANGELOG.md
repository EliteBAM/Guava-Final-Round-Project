# Changelog

Changes made to the Intake CRM after its first version (0.1.0), recorded so the project can be handed back to whoever built it.

## 2026-10-08 (final): PDF previews fixed

**Made by:** Claude Code, in the main app's repository.

**Why:** every thumbnail in the Document Library, and the preview in the details dialog, showed "Preview unavailable". This dates from 0.1.0.

- **Cause:** `renderThumb()` in `public/app.js` called `pdf.destroy()` after rendering. In pdf.js 6, the loaded document no longer has `destroy()`; it is on the loading task. The page rendered, but the throw in `finally` rejected the result, so the fallback was shown.
- **Fix:** keep the loading task from `getDocument()` and call `task.destroy()` in the `finally`. Awaiting `task.promise` inside the `try` also frees the worker when a PDF fails to load. `fillPage()` now logs `console.warn('PDF preview failed', err)` before showing the fallback, so a future failure shows its reason.
- **Checked:** in headless Chrome 154 against the running server, the library shows 4 of 4 thumbnails (it was 0 of 4), the dialog preview renders, and the console has no warnings.

## 2026-10-08 (latest): documents sent by email

**Made by:** Claude Code, in the main app's repository.

**Why:** the main app can't text yet, because its phone number needs carrier SMS registration. DocuSign now emails the caller the signing link instead.

- **`public/app.js`:** `documentsCard()` reads a new `sentVia` field. With `email`, the *Sent* row shows "By email to {address}". Anything else keeps the "By text to •••• 1234" format.
- **Docs:** `2-API.md` lists `sentVia`, and `sentTo` can now be an email address.
- **No server or database change:** the documents column already stores whatever fields the main app sends.

## 2026-10-08 (later): signing-packet status

**Made by:** Claude Code, in the main app's repository.

**Why:** the main app now texts callers a DocuSign signing link for the Statement of Client's Rights, the fee agreement and the HIPAA authorization. Intake staff need to see whether the documents went out and whether the client has signed.

- **`lib/db.js`:** a new `documents` column (JSON), added to existing databases by `migrate()`. `mergePncDocuments(callId, changes)` shallow-merges into it and returns `null` when there's no PNC for the call. `toPnc` adds `documents`.
- **`server.js`:** `PATCH /api/v1/pncs/{callId}/documents`. It returns `200` with the PNC, `404` when no PNC exists for the call, and `405` for any other method, and it broadcasts `pnc-updated`. The column is separate from `record`, so the main app's `PUT` at the end of a call never overwrites it.
- **`public/app.js`:** `documentsCard()` replaces the static "Not sent yet" card. It shows the status, who it was texted to and when, when the client signed, the document names and the envelope ID. With no status, the dashed "Not sent yet" card is still shown.
- **Docs:** `2-API.md`, `1-Overview.md` and `PRODUCT.md`.
- **Checked:** with curl on a throwaway data folder: an unknown call gets `404`; `sent` followed by `client_signed` merges into one status; a later `PUT` keeps it; a wrong method gets `405`.
- **Not done:** the attorney's countersignature isn't reported back, because DocuSign Connect webhooks would need another public endpoint. The card says the countersignature was requested by email.

## 2026-10-08: intake records, document kinds, template seeding

**Made by:** Claude Code, working in the main app's repository (the Guava legal-intake voice agent).

**Why:** the main app is getting ready to text callers their signing documents. It needs to find the right templates in the CRM's library reliably, and to send each call's full intake record so intake staff can see it. The PNC page's "Not yet defined" placeholders are now filled from that record.

### Data (`lib/db.js`, new `lib/paths.js`)
- **New PNC columns:**
  - `call_id`: the main app's call ID, with a unique index;
  - `record`: the intake record, as JSON text;
  - `updated_at`.
- **New document column:** `kind`, with a unique index. NULLs don't clash, so documents added by hand are unaffected.
- **Upgrade in place:** `migrate()` adds any missing column with `ALTER TABLE ... ADD COLUMN` when the database opens, so an existing `data/intake.db` is upgraded without losing rows. This was tested on a copy of a 0.1.0 database. SQLite can't add a UNIQUE column, which is why uniqueness is an index.
- **New queries:** `upsertPncByCall()` (returns `{ pnc, created }`) and `getDocumentByKind()`. `createPnc()` now also sets `updated_at`, and `createDocument()` accepts `kind`.
- **API objects:** PNCs gain `updatedAt`, `callId` and `record` (parsed). Documents gain `kind`.
- **`lib/paths.js`:** holds `ROOT`, `DATA_DIR`, `DOCS_DIR`, `DB_FILE` and `docPath()`, so the server and the seed script agree. `DATA_DIR` can now be overridden with an environment variable of the same name, for test runs.

### API (`server.js`)
- **New:** `PUT /api/v1/pncs/{callId}`, with a body of `{ name, summary, record }`.
  - It creates a PNC (`201`) or updates the one for that call ID (`200`), and broadcasts `pnc-created` or `pnc-updated`.
  - `callId` must match `^[A-Za-z0-9._:-]{1,200}$`, and `record` must be a JSON object or absent. Anything else gets `400`. Any other method gets `405`.
- `GET /api/v1/documents` now includes `kind`.
- `POST /api/v1/pncs` is unchanged.
- The data paths now come from `lib/paths.js`. There is no other server change.

### Seeding (new `seed.js`, `npm run seed`)
- Copies the four template PDFs from `../Assets` (the main repository's folder) into the library: Statement of Client’s Rights, Contingency Fee Agreement, HIPAA Authorization and Client Questionnaire. Each is tagged with its kind.
- It skips any kind already present, so it is safe to run again.
- It writes through `lib/db.js` directly, not over HTTP. `ASSETS_DIR` overrides the source folder.
- It has been run once on this PC, so the four templates are already in `data/`.

### UI (`public/app.js`, `public/app.css`, `public/index.html`)
- **PNC detail view:** the three dashed placeholders are replaced by:
  - the disposition in the header, plus "Updated …" when the record changed after it arrived;
  - *Flags for the attorney*, as neutral chips;
  - *Intake record*: seven cards, one per record section. Labels and values are made readable through `FIELD_LABELS`, `VALUE_LABELS`, `FLAG_LABELS` and `humanize()`. ISO dates are shown as dates, and `narrative` is hidden because it is the summary.
  - *Missing information*;
  - *Documents*: a dashed "Signing packet · Not sent yet" card, for the e-signature step.
- **Empty sections:** a section with nothing in it, including every section of a PNC added by hand, shows a dashed *Not collected* card. That follows DESIGN.md's rule that dashed borders mark empty areas.
- **Live updates:** a new `pnc-updated` event replaces the PNC in place (`updatePnc()`).
- **Document cards and details:** the card shows the kind in monospace, truncated with the full value on hover. The details dialog gains a *Kind* row.
- **Removed:** the CSS for `.placeholder-grid` and `.placeholder`, which are no longer used. The new CSS is in the PNC section of `app.css`, using the existing tokens. No new colours were added. The flags are deliberately neutral, per the One Ink and Meaningful Red rules.

### Docs
- `Documents/1-Overview.md`, `Documents/2-API.md` and `PRODUCT.md` are updated to match.
- This changelog is new.

### Checked
- Seeding twice gives 4 documents with no duplicates.
- On the API, a `PUT` to the same call ID twice gives 1 PNC, returning `201` then `200`. A bad call ID or record gets `400`, the wrong method `405`, and a missing key `401`. `POST /pncs` still works.
- The PNC page and the library were screenshotted in headless Chrome with a real record from the main app.

### Not done (left for later)
- Nothing in the CRM writes to the Documents section yet. *(Done in the later entry above: `PATCH /pncs/{callId}/documents`.)*
- Documents added by hand have no way to set a kind in the UI. Only the seed script sets kinds.
- The UI routes (`/app/*`) still have no authentication. The server must stay on `127.0.0.1`.
