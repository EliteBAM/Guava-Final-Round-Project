# Documents and Data Stack

What paperwork the intake produces, which templates we keep and why, and how one call's data moves from the voice agent to the CRM (and, next, to DocuSign and the caller's phone).

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
| **Signing packet** | The client signs, then the attorney countersigns | **Templates:** `statement-of-client-rights`, `contingency-fee-agreement` and `hipaa-authorization`, sent through DocuSign (next phase). |

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

| Anchor | Field | Filled by | DocuSign tab (planned) | In |
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

**Planned (DocuSign and SMS phase):**

```
next_steps task: permission to text, and a confirmed number
  └─ worker: GET /api/v1/documents → pick by kind → download the three signing-packet PDFs
       └─ DocuSign: one envelope, Statement first, anchor tabs, client at routing order 1, attorney at 2
            └─ guava.Client().send_sms(from = call.call_info.to_number, to = caller)
                 with a link to our redirect page (via ngrok), which opens a fresh signing session on each tap
            └─ envelope status → the PNC's Documents section
```

---

## 4. CRM API surface

The base is `http://127.0.0.1:3000/api/v1`, with an `X-API-Key` header. The full reference is `Intake CRM/Documents/2-API.md`.

| Endpoint | Purpose | Used by | Status |
|---|---|---|---|
| `POST /pncs` | Create a PNC (name and summary) | Manual tests | Original |
| `PUT /pncs/{callId}` | Create or update a PNC with the full intake record | `Application/crm.py` | **New** |
| `GET /documents` | List the templates, with their `kind` | The DocuSign worker | `kind` is **new** |
| `GET /documents/{id}` | Download a template PDF | The DocuSign worker | Original |
| Set the PNC's document status | Show the envelope's status on the PNC | The DocuSign worker | **Planned** (not built) |

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

| Variable | Read by | Default |
|---|---|---|
| `CRM_API_URL` | `Application/crm.py` | `http://127.0.0.1:3000/api/v1` |
| `CRM_API_KEY` | `Application/crm.py` | The contents of `Intake CRM/data/api-key.txt` |
| `CONFLICT_API_URL` | `Application/conflicts.py` | `http://127.0.0.1:8787` (`mock_api.py`) |
| `PORT` | The CRM server | `3000` |
| `DATA_DIR` | The CRM server and `seed.js` | `Intake CRM/data` |
| `ASSETS_DIR` | `seed.js` | `Assets/` |

---

## 7. Open items

- **DocuSign:** create the app's integration key and an RSA key pair, add a redirect URI, and grant consent once (JWT auth). This is the user's step, in the developer account.
- **ngrok:** a free account and the install, to expose the one redirect page.
- **SMS:** confirm the Guava number can send texts, which needs A2P 10DLC registration, with one test text to your own phone.
- **CRM:** a way to record the envelope's status on a PNC (for example `PATCH /pncs/{callId}`, or a `documents` key inside `record`). The changelog lists this as not done.
- **Live tests:** they post their PNCs to the CRM when it's running, because `on_session_end` runs in live tests too. The CRM has no PNC delete. If test PNCs pile up, stop the CRM, delete `Intake CRM/data/`, then start it and run `npm run seed` again. You get a new API key, which `crm.py` picks up from the file.
