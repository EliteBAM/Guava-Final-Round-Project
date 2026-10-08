# Documents and Data Stack

What paperwork the intake produces, which templates we keep and why, and how one call's data moves from the voice agent to the CRM, DocuSign and the caller's inbox.

Related:
- `../Legal Intake Specialist Agent Notes/PI Intake Research.md`: the research behind the documents (section 1).
- `../Legal Intake Specialist Agent Notes/Story Stage Schema and Plan.md`: the record's fields and shape.
- `../../Intake CRM/Documents/`: the CRM's own docs and changelog.

---

## 1. The intake documents and how each is handled

The research found five documents around a personal injury intake (PIR section 1).

| Document | Who fills it in, and when | How we handle it |
|---|---|---|
| **Intake sheet / lead record** | The intake specialist, during the call | **Data, not a PDF.** The agent's fields, built into the record by `intake.build_record`, shown as the PNC's *Intake record* cards in the CRM. |
| **Intake summary** | Written for the reviewing attorney, right after the call | **Data, not a PDF.** It differs on every call. The narrative is the PNC's *Summary*; flags and missing information are their own sections. |
| **Client questionnaire** | The client, after signing | **Template:** `client-questionnaire`. It sits in the library; sending it is a later phase. |
| **Motor-vehicle supplement** | The client, after signing | **Merged into the questionnaire** as section 6, rather than a separate form. |
| **Signing packet** | The client signs, then the attorney countersigns | **Templates:** `statement-of-client-rights`, `contingency-fee-agreement` and `hipaa-authorization`, emailed to the caller by DocuSign during the call, as one envelope (section 3). |

**Skipped from the signing packet:**
- **Letter of representation.** The firm sends it to the insurers after the case is accepted; it isn't something the client signs on intake.
- **Medicare (CMS) forms.** Too specialized for the MVP. The questionnaire asks whether the client is on Medicare, which is what tells the team to send them.

---

## 2. The four templates (`Assets/`)

All four are marked **SAMPLE**, with a watermark and a note: "for a software demonstration, not issued by or affiliated with Morgan & Morgan, not legal advice".

| File | CRM kind | Pages | Content and source |
|---|---|---|---|
| `statement-of-client-rights` | `statement_of_client_rights` | 2 | The Florida Bar's official text, **verbatim**, from Rule 4-1.5(f)(4)(C), *Rules Regulating The Florida Bar* (version of October 1, 2026). Client and attorney sign it before the contract. |
| `contingency-fee-agreement` | `fee_agreement` | 3 | **Mock agreement in plain language.** It includes:<ul><li>the two clauses Rule 4-1.5(f)(4)(A)(i) and (ii) require, **verbatim** ("received and read the statement", and the 3-business-day cancellation);</li><li>the fee schedule at the Rule 4-1.5(f)(4)(B)(i) caps;</li><li>the fee on the gross recovery, as Statement item 6 asks the lawyer to say;</li><li>costs, liens and the closing statement;</li><li>settlement consent, other lawyers, and no guarantee;</li><li>"takes effect only when both the client and an attorney have signed", which matches the agent's `NEXT_STEPS_SCRIPT`.</li></ul> |
| `hipaa-authorization` | `hipaa_authorization` | 1 | **Mock authorization** covering the core elements and required statements of 45 CFR 164.508(c):<ul><li>who releases, who receives, what, why, and when it ends;</li><li>the right to revoke, no conditioning of treatment, possible re-disclosure, and a copy for the patient.</li></ul> It excludes psychotherapy notes. Records of substance use, mental health and HIV are released only if the client initials. |
| `client-questionnaire` | `client_questionnaire` | 3 | **Built from `intake.DEFERRED`**: the items the agent tells callers "the team will send on a short form". Sections: about you, medical providers, health insurance, work and wages, earlier accidents, the motor-vehicle supplement (vehicle, police report, auto policy and UM limits, other driver, relatives' auto insurance), and documents. It deliberately doesn't ask for a Social Security number. |

**Verified:** the Statement's 12 paragraphs and the agreement's two required clauses were compared by script against the text extracted from the Bar's Chapter 4 PDF (<https://www-media.floridabar.org/uploads/2026/10/2027_04-OCT-Chapter-4-RRTFB.pdf>). All match word for word. **Don't edit them.**

### DocuSign anchors

Each template carries hidden anchor strings: white 7pt text at the spot where a field goes. They're invisible on the page but present in the PDF's text layer. When the envelope is created, DocuSign places a tab at **every** occurrence of an anchor across the envelope, so one tab definition covers all the documents.

| Anchor | Field | Filled by | DocuSign tab (`esign.py`) | In |
|---|---|---|---|---|
| `\c_name\` | Client's full name | Code, from the call (locked) | Text, or FullName | all four |
| `\c_sign\` | Client signature | Client | SignHere | all four |
| `\c_date\` | Client's signing date | DocuSign | DateSigned | all four |
| `\c_init\` | Initials to release sensitive records | Client (optional) | InitialHere | HIPAA |
| `\c_dob\` | Date of birth (not asked on the call) | Client | Text | HIPAA |
| `\i_date\` | Incident date | Code, from the call (locked) | Text | fee agreement, HIPAA |
| `\s_date\` | Date prepared (today) | Code (locked) | Text | fee agreement |
| `\a_sign\` | Attorney signature | Attorney, routing order 2 | SignHere | Statement, fee agreement |
| `\a_name\` | Attorney's printed name | DocuSign | FullName | fee agreement |
| `\a_date\` | Attorney's signing date | DocuSign | DateSigned | Statement, fee agreement |

### Changing a template
1. Edit the `.html` file, or the shared `document.css`.
2. Run `powershell -ExecutionPolicy Bypass -File Assets\build-pdfs.ps1`. It prints every `.html` to `.pdf` with headless Chrome or Edge, whichever is installed. This PC has Chrome only.
3. In the CRM, trash the old copy from the Document Library, then run `npm run seed` in `Intake CRM/`. The seed script skips any kind that's still in the library.

---

## 3. How a call's data moves

```
Guava call fields (call.get_field)
  └─ main.on_session_end → write_intake_record
       └─ intake.build_record(fields, state, call.id)        the record (Story Stage Schema and Plan 1.5)
            ├─ Application/intake_records/{call_id}.json      always written
            └─ crm.upsert_pnc  (worker thread)                 PNCs only, see below
                 └─ PUT /api/v1/pncs/{call_id}  → Intake CRM: SQLite → PNC page, live
```

**Which calls become PNCs:** a PNC is a potential new client, so the agent sends the record only when both of these hold:
- the triage answer is `new_injury_matter`, or there's no triage answer yet (the call ended before triage);
- the caller gave a name.

Callers routed to other teams (existing clients, adjusters, providers, other matters) are written to the JSON file only.

**The signing packet, during the call** (`main.py`: `next_steps` → `send_documents` → `documents_sent` or `documents_follow_up`):

```
next_steps: the agent asks for an email address (spelled, then read back), or "none"
  └─ send_documents (worker thread)
       ├─ crm.upsert_pnc            the PNC exists mid-call (the full record replaces it at session end)
       ├─ crm.fetch_templates       GET /documents → by kind → the three PDFs, Statement first
       ├─ esign.create_envelope     a draft: anchor tabs, client embedded (routing 1), attorney by email (routing 2)
       ├─ signing_server.link_for   {SIGNING_PUBLIC_URL}/sign/{envelope}/{hmac}
       ├─ esign.send_envelope       the link becomes the client's embeddedRecipientStartURL, then status "sent":
       │                            DocuSign emails the caller, and the email's button opens our link
       └─ crm.update_documents      PATCH /pncs/{callId}/documents {status: sent, sentVia: email, sentTo, ...}
  ├─ documents_sent: "did that email come through?", the verbatim next-steps line, offer an attorney
  └─ documents_follow_up (declined, or any step failed): "the team will send them", same line; flag documents_not_sent

Caller clicks the email's button (DocuSign → ngrok → signing_server on 127.0.0.1:3001)
  └─ HMAC checked → esign.signing_url → 302 to a fresh DocuSign session (DocuSign's own URLs last minutes)
       └─ DocuSign returns to /done?event=signing_complete → esign.client_signed confirms
            → PATCH documents {status: client_signed} → thank-you page; DocuSign emails the attorney to countersign
```

**Why the client is "embedded" yet still gets DocuSign's email:**
- An embedded signer (`clientUserId`) signs through our page, so we get the `/done` return and can update the CRM.
- Setting `embeddedRecipientStartURL` makes DocuSign send the invitation email anyway, and points its button at our page. DocuSign calls this hybrid signing.
- Our link contains the envelope ID, so the envelope is created as a draft, given the link, and then sent.

No envelope is made unless DocuSign is configured, so tests take the follow-up path. The attorney's countersignature isn't reported back yet, because that would need DocuSign Connect webhooks.

**Texting:** `texting.py` (`guava.Client().send_sms`) is built and tested, but the call doesn't use it yet. Guava refuses the send: `400 SMS is not configured on +14843040566. No CarrierX messaging service ID on the use case.` The fix is account-side (section 7). Check it with `python -m texting +1XXXXXXXXXX`.

---

## 4. CRM API surface

The base is `http://127.0.0.1:3000/api/v1`, with an `X-API-Key` header. The full reference is `Intake CRM/Documents/2-API.md`.

| Endpoint | Purpose | Used by | Status |
|---|---|---|---|
| `POST /pncs` | Create a PNC (name and summary) | Manual tests | Original |
| `PUT /pncs/{callId}` | Create or update a PNC with the full intake record | `Application/crm.py` | **New** |
| `GET /documents` | List the templates, with their `kind` | The DocuSign worker | `kind` is **new** |
| `GET /documents/{id}` | Download a template PDF | The DocuSign worker | Original |
| `PATCH /pncs/{callId}/documents` | The signing packet's status (sent, client_signed) | `crm.update_documents` | **New** |

---

## 5. Where data lives

| Path | Contents | In git? |
|---|---|---|
| `Assets/` | The template HTML, `document.css`, the PDFs and `build-pdfs.ps1` | Yes |
| `Application/intake_records/` | One JSON record per call, containing callers' personal details | No (`.gitignore`) |
| `Intake CRM/data/intake.db` | PNCs (with records) and the document list | No (`.gitignore`) |
| `Intake CRM/data/documents/` | The library's PDFs, the seeded copies of `Assets/` | No (`.gitignore`) |
| `Intake CRM/data/api-key.txt` | The CRM's API key | No (`.gitignore`) |

---

## 6. Configuration

These settings live in `Application/.env` (or a `.env` at the repo root). `main.py` and `python -m esign` load it; tests never do. `KEY=value` and `export KEY=value` lines both work.

| Variable | Read by | Default |
|---|---|---|
| `CRM_API_URL` | `Application/crm.py` | `http://127.0.0.1:3000/api/v1` |
| `CRM_API_KEY` | `Application/crm.py` | The contents of `Intake CRM/data/api-key.txt` |
| `CONFLICT_API_URL` | `Application/conflicts.py` | `http://127.0.0.1:8787` (`mock_api.py`) |
| `DOCUSIGN_INTEGRATION_KEY`, `DOCUSIGN_USER_ID`, `DOCUSIGN_ACCOUNT_ID` | `Application/esign.py` | none (required) |
| `DOCUSIGN_PRIVATE_KEY_PATH` | `Application/esign.py` | `Application/docusign_private.key` (gitignored by `*.key`) |
| `ATTORNEY_NAME`, `ATTORNEY_EMAIL` | `Application/esign.py`: the countersigning attorney | none (required) |
| `SIGNING_PUBLIC_URL`, `SIGNING_SECRET` | `Application/signing_server.py`: the ngrok address and the link-signing key | none (required for links) |
| `SMS_ENABLED` | `Application/texting.py` (its command-line check only; the call emails) | off: texts are only sent when it's `1` |
| `GUAVA_AGENT_NUMBER` | `python -m texting`: the number it texts from | `+14843040566` |
| `PORT` | The CRM server | `3000` |
| `DATA_DIR` | The CRM server and `seed.js` | `Intake CRM/data` |
| `ASSETS_DIR` | `seed.js` | `Assets/` |

---

## 7. Open items

- **SMS:** blocked on both sides, so the call emails instead.
  - **Guava** needs four approvals on its Compliance page before `send_sms` works: Outbound Dialing registration, then a use case, then an SMS brand registration, then an SMS campaign registration (A2P 10DLC). See <https://goguava.ai/docs/outbound-and-sms-permissions.md>.
  - **DocuSign's own SMS delivery** is off on the sandbox (`allowSMSDelivery = false`), and turning it on needs DocuSign's approval.
  - Once Guava's registration is approved, texting the same link is a small change in `main.send_documents`.
- **Attorney countersignature:** not reported back to the CRM. That would need DocuSign Connect webhooks, or polling.
- **Questionnaire:** in the library, but not sent yet.

**Running the full demo:** start the CRM (`npm start` in `Intake CRM`), `mock_api.py`, `ngrok http 3001 --url=<your domain>`, then `python -m main` in `Application`. `python -m esign you@example.com`, with ngrok running, does a sandbox dry run without a call: it emails you a test envelope and serves the signing page until you press Enter.
- **Live tests:** they post their PNCs to the CRM when it's running, because `on_session_end` runs in live tests too. The CRM has no PNC delete. If test PNCs pile up, stop the CRM, delete `Intake CRM/data/`, then start it and run `npm run seed` again. You get a new API key, which `crm.py` picks up from the file.
