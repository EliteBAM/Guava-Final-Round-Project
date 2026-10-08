# Intake CRM: API

**Base URL:** `http://127.0.0.1:3000/api/v1`

Every request needs the API key. Bodies and responses are JSON, except document downloads, which return the PDF itself.

## Quickstart

Start the server (`npm start`), then in PowerShell from the project folder:

```powershell
# 1. Read the API key
$h = @{ 'X-API-Key' = (Get-Content data\api-key.txt).Trim() }

# 2. Create a PNC
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:3000/api/v1/pncs -Headers $h `
  -ContentType 'application/json' -Body '{"name":"Jordan Ellis","summary":"Rear-ended at a stop light."}'

# 3. List documents, then download the first one (add a PDF in the UI first)
$docs = Invoke-RestMethod -Uri http://127.0.0.1:3000/api/v1/documents -Headers $h
Invoke-WebRequest -Uri "http://127.0.0.1:3000/api/v1/documents/$($docs[0].id)" -Headers $h -OutFile template.pdf
```

The same calls with curl:

```
curl -X POST http://127.0.0.1:3000/api/v1/pncs -H "X-API-Key: <key>" -H "Content-Type: application/json" -d "{\"name\":\"Jordan Ellis\"}"
curl http://127.0.0.1:3000/api/v1/documents -H "X-API-Key: <key>"
curl http://127.0.0.1:3000/api/v1/documents/<id> -H "X-API-Key: <key>" -o template.pdf
```

## API key

- **Where it comes from:** the server creates a random key the first time it starts and saves it to `data/api-key.txt`. It also prints the key at every startup.
- **How to send it:** in the `X-API-Key` header on every `/api/v1` request. A missing or wrong key gets `401`.
- **How to change it:** delete `data/api-key.txt` and restart the server.
- **What it doesn't cover:** the browser UI uses internal `/app/*` routes that don't check the key. That's only safe because the server listens on this PC alone. Don't expose it to a network as it stands.

## Endpoints

### `POST /pncs`: create a PNC

Send it with `Content-Type: application/json`. The body can be at most 64 KB.

| Field | Type | Rules |
|---|---|---|
| `name` | string | Required. Surrounding spaces are trimmed. Must not be empty and can be at most 200 characters. |
| `summary` | string | Optional. Trimmed. At most 5000 characters. |

Any other fields are ignored.

**`201 Created`.** The new PNC also appears live in the UI.

```json
{
  "id": "c972bc31-aeaf-4588-b6e5-9629e3893876",
  "name": "Jordan Ellis",
  "summary": "Rear-ended at a stop light.",
  "source": "api",
  "createdAt": "2026-10-08T09:03:22.205Z"
}
```

**Errors:**
- `400`: missing or invalid field, or the body isn't valid JSON.
- `401`: bad or missing key.
- `413`: body too large.
- `415`: wrong `Content-Type`.

### `PUT /pncs/{callId}`: create or update a PNC by call ID

This is how the main app sends each call's intake record. It is keyed on the main app's call ID, so sending the same call again updates its PNC instead of creating a duplicate.

- **`callId`:** 1 to 200 letters, digits, or `.` `_` `:` `-` characters.
- **Body:** send it with `Content-Type: application/json`. It can be at most 64 KB.

| Field | Type | Rules |
|---|---|---|
| `name` | string | Required. Same rules as `POST /pncs`. |
| `summary` | string | Optional. Same rules as `POST /pncs`. |
| `record` | object | Optional. The intake record, stored as sent and shown on the PNC's page. See *The intake record* below. |

**`201 Created`** for a new PNC, **`200 OK`** for an update. Either way the PNC appears or refreshes live in the UI.

```json
{
  "id": "fbb31e90-9715-4164-a815-8f9e265f9b02",
  "name": "Ana Lopez",
  "summary": "Rear-ended at a red light.",
  "source": "api",
  "createdAt": "2026-10-08T10:16:49.944Z",
  "updatedAt": "2026-10-08T10:16:49.996Z",
  "callId": "2143386266938584",
  "record": { "disposition": "pending_signature", "...": "..." }
}
```

**Errors:** as for `POST /pncs`, plus `400` when the call ID or `record` isn't valid.

#### The intake record

The main app builds it (`intake.build_record` in the agent). The PNC page shows these parts of it; any other keys are stored but not shown.

| Key | Shown as |
|---|---|
| `disposition` | The disposition under the PNC's name |
| `caller`, `incident`, `injuries`, `liability`, `coverage`, `parties`, `conflicts` | One card each, listing every field in it. Choice values such as `er_or_hospital` are shown as "ER or hospital", and dates as dates. |
| `flags` | Chips under *Flags for the attorney* |
| `completeness.critical_missing`, `completeness.important_missing` | *Missing information* |

### `GET /documents`: list documents

**`200 OK`**, newest first:

```json
[
  { "id": "352bb17f-c796-40e2-8060-4182180ffad0", "name": "Contingency Fee Agreement", "kind": "fee_agreement", "size": 128270, "createdAt": "2026-10-08T09:03:22.266Z" }
]
```

`kind` is how the main app finds a template, whatever its display name. It is `null` for documents added by hand. `npm run seed` sets these kinds:

| `kind` | Document |
|---|---|
| `statement_of_client_rights` | Statement of Client’s Rights |
| `fee_agreement` | Contingency Fee Agreement |
| `hipaa_authorization` | HIPAA Authorization |
| `client_questionnaire` | Client Questionnaire |

### `GET /documents/{id}`: download a document

**`200 OK`** returns the PDF itself:
- `Content-Type: application/pdf`
- `Content-Disposition: attachment; filename="<name>.pdf"`

**`404`** if no document has that ID.

## Errors

Every error comes back as JSON with a readable message:

```json
{ "error": "\"name\" is required." }
```

| Status | Meaning |
|---|---|
| `400` | Invalid input or malformed JSON |
| `401` | Missing or invalid API key |
| `404` | Unknown route or document ID |
| `405` | Wrong HTTP method for the route |
| `413` | Request body too large |
| `415` | Body isn't JSON (`POST /pncs`, `PUT /pncs/{callId}`) |
| `421` | Unexpected `Host` header. Use `127.0.0.1` or `localhost` with the server's port. |
| `500` | Server error. Check the server's terminal. |

## Data types

- `id`: a UUID string.
- `createdAt`, `updatedAt`: ISO-8601 timestamps in UTC.
- `callId`: the main app's call ID, or `null` for PNCs made by `POST /pncs` or by hand.
- `size`: in bytes.
- `source`: `"api"` or `"manual"`. Manual means it was added by hand in the UI.
