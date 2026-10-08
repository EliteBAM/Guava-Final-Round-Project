# Story Stage: Intake Schemas and Implementation Plan

Built from `PI Intake Research.md` (PIR). It works backward: the documents the attorney receives define the fields, and the fields' tiers define the questioning and the "done" condition.

---

## Part 1: The documents as schemas

The call produces two documents (PIR §1). The other three (MVA supplement, client questionnaire, signing packet) are post-call. Their fields are listed only as `DEFERRED`, so the attorney sees what is still to be collected.

### 1.1 Field spec (one definition drives both the Guava field and the record)

```python
@dataclass(frozen=True)
class FieldSpec:
    key: str
    kind: str                      # "text" | "multiple_choice" | "date"
    ask: str                       # what to collect, in plain words (becomes the Guava description)
    tier: str                      # "critical" | "important"  (no "opportunistic": live finding 2)
    section: str                   # record section: incident | liability | injuries | coverage | parties
    choices: tuple[str, ...] = ()
    when: str = ""                 # applicability note, e.g. "only if they've had treatment"
```

**Tier → Guava `Field` mapping** (my helper, not an SDK API):

| Tier | `required` | Added to the description |
|---|---|---|
| critical | `True` | "If they don't know, record that (unsure / unknown); don't press." |
| important | `False` | "Ask once if they haven't already mentioned it. Accept 'I don't know'." |
| ~~opportunistic~~ | — | **Removed after live testing**; see the second live finding below |

Critical multiple-choice fields always include a `not_sure` choice, so "I don't know" can complete a required field.

**Live finding 2 (implemented): no "never ask" tier.** Guava fires `on_task_complete` once every checklist item is *resolved*. An optional field resolves only by a value, or by the caller declining it, which requires asking. An opportunistic field ("only record if they mention it; don't ask") therefore has no way to resolve. Usually the model skipped it anyway, but in one live run it waited and the story task never completed. The two opportunistic fields, `police_agency` and `vehicle_damage`, are removed from the call. When the caller volunteers them they're in the `narrative`; otherwise they're listed in `DEFERRED` for the questionnaire. Every checklist item now resolves the same way: ask once, and any answer counts, including "unknown".

**Live finding 1 (implemented):** every *asked* field needs a "don't know" value, whatever its tier:
- multiple choice: `not_sure`;
- text: `"unknown"`;
- date: the caller's best estimate, or skip.

An optional field the agent asked about but couldn't fill kept the task from completing, and the agent stalled until the session ended. This was seen with `other_insurer` and with an approximate `discovery_date`. `unknown_hint()` in `main.py` adds this guidance to every field description.

### 1.2 Intake sheet: common core (task `story`)

| key | kind | tier | section | choices / note |
|---|---|---|---|---|
| narrative | text | critical | incident | their account, in their words |
| incident_type | mc | critical | incident | motor_vehicle, slip_and_fall, medical_or_nursing_home, other |
| incident_state | mc | critical | incident | florida, other_state |
| incident_location | text | critical | incident | city/county, plus street or intersection if known |
| injuries | text | critical | injuries | body parts and symptoms, in their words |
| treatment | mc | critical | injuries | er_or_hospital, doctor_or_urgent_care, none_yet |
| first_treatment_date | date | critical* | injuries | *only if treated (stays `required=False`, enforced by the description and the existing validator) |
| still_treating | mc | important | injuries | yes, no, not_sure |
| missed_work | mc | important | injuries | yes, no, not_working |
| police_report | mc | critical | liability | yes, no, not_sure |
| ~~police_agency~~ | — | — | — | removed from the call (live finding 2); in the narrative if volunteered, otherwise on the questionnaire |
| witnesses | mc | important | liability | yes, no, not_sure |
| photos | mc | important | liability | yes, no, not_sure |
| government_involved | mc | critical | parties | yes, no, not_sure |
| other_parties | text | critical† | parties | †may be empty; it feeds the conflict re-check. Answers meaning "nobody" / "unknown" (the model writes "none" rather than leaving it empty) are filtered in code by `intake.named_parties`, conservatively, so a real name is never skipped |
| insurer_contact | mc | important | coverage | gave_statement, contacted_only, no_contact, not_sure (the other side's insurer) |
| prior_similar_injury | mc | important | injuries | yes, no, not_sure (a prior injury or claim involving the same body part) |

### 1.3 Motor-vehicle module (task `details_mva`)

| key | kind | tier | section | choices / note |
|---|---|---|---|---|
| vehicle_role | mc | critical | incident | driver, passenger, pedestrian, cyclist, motorcyclist |
| other_vehicle | mc | critical | parties | personal, commercial_or_work, rideshare, hit_and_run, not_sure |
| on_the_job | mc | critical | parties | yes, no (the caller was working at the time) |
| seat_belt | mc | important | liability | yes, no, not_sure, not_applicable (ask plainly, no commentary) |
| ambulance | mc | important | injuries | yes, no |
| other_insurer | text | important | coverage | "unknown" is fine |
| own_insurer | text | important | coverage | their auto insurer. "none" if uninsured, "unknown" if they don't know; the attorney needs to tell these apart (no PIP vs. unknown PIP) |
| um_coverage | mc | important | coverage | yes, no, not_sure |
| ~~vehicle_damage~~ | — | — | — | removed from the call (live finding 2); in the narrative if volunteered, otherwise on the questionnaire |

### 1.4 Stub modules

`details_premises` (slip_and_fall, Fla. Stat. 768.0755):

| key | kind | tier | choices |
|---|---|---|---|
| property_type | mc | critical | business, residence, government, other |
| hazard | text | critical | what caused the fall |
| reported_to_staff | mc | important | yes, no, not_sure |
| incident_report | mc | important | yes, no, not_sure |

`details_medical` (medical_or_nursing_home; it adds the `route_nurse_intake` flag, and an RN screener follows up):

| key | kind | tier | choices |
|---|---|---|---|
| provider_name | text | critical | the doctor, hospital or facility |
| discovery_date | text | important | roughly when they realised something was wrong (Fla. Stat. 95.11(5)(c)). Text, not date: callers give approximate times, and a date field stalled live |

`other` has no module and goes straight to qualify, with the `non_mva_case_type` flag.

### 1.5 Intake summary / record (for attorney review)

The record is built by pure code from the sheet and the call state when the session ends. No model is involved. It's written as one JSON per call.

```jsonc
{
  "call_id": "...", "created_at": "2026-10-08T14:02:11-04:00",
  "disposition": "pending_signature",
  "caller": {"name": "Ana Lopez", "recording_consent": "yes"},
  "conflicts": {"status": "clear", "names_checked": ["Ana Lopez", "Mark Davis"], "recheck": "not_needed"},
  "incident": {"type": "motor_vehicle", "date": "2026-09-30", "state": "florida", "location": "...", "narrative": "..."},
  "liability": {"police_report": "yes", "witnesses": "not_sure", "photos": "yes", "seat_belt": "yes", ...},
  "injuries": {"injuries": "...", "treatment": "er_or_hospital", "first_treatment_date": "2026-09-30", ...},
  "coverage": {"other_insurer": "unknown", "own_insurer": "GEICO", "um_coverage": "not_sure", ...},
  "parties": {"adverse": "Mark Davis", "other_vehicle": "personal", "government_involved": "no", ...},
  "flags": ["sol_urgent", ...],
  "completeness": {"critical_missing": [], "important_missing": ["witnesses"]},
  "deferred_to_questionnaire": ["policy numbers and limits", "provider list and bills", "employer and wages", ...]
}
```

The sections are the attorney's four decision drivers (PIR takeaway 4). `completeness` is the code-side audit: like the next-steps phrase audit, it is a flag and not a gate.

### 1.6 New qualification flags (pure, in `qualification.py`)

| Flag | Rule |
|---|---|
| `commercial_vehicle` | other_vehicle = commercial_or_work |
| `rideshare` | other_vehicle = rideshare |
| `hit_and_run` | other_vehicle = hit_and_run |
| `on_the_job` | on_the_job = yes (workers' comp overlap) |
| `statement_given` | insurer_contact = gave_statement |
| `prior_similar_injury` | prior_similar_injury = yes |
| `no_seat_belt` | seat_belt = no |

None of these is spoken, and none of them declines a case.

---

## Part 2: Implementation plan

### 2.1 Graph change: Story splits into narrative + module details

```
Story --> module: narrative + core collected
state module <<choice>>                      (code: incident_type)
module --> DetailsMVA: motor_vehicle
module --> DetailsPremises: slip_and_fall
module --> DetailsMedical: medical_or_nursing_home
module --> qualify: other
DetailsMVA / DetailsPremises / DetailsMedical --> qualify
```

**Why it changes from the earlier one-task decision:** the field count roughly doubles, and roughly half the fields depend on the case type. A code branch on the typed `incident_type` (graph rule 4) is cleaner than ten "if not a car accident, choose not_applicable" descriptions. The module task still sees the whole conversation, so it can fill fields from what the caller already said.

**Risk:** the module task may re-ask things the caller already said. The live test checks this. If it does, the fallback is one task containing the core plus the matching module's fields only. The checklist is still built in code from `incident_type`, so the only difference is where the branch happens.

### 2.2 Files

| File | Change |
|---|---|
| `Application/intake.py` (new, pure, no Guava) | `FieldSpec`; `CORE`, `MODULES = {"motor_vehicle": MVA, ...}`; `DEFERRED`; `completeness(fields, specs)`; `build_record(fields, state)` |
| `Application/main.py` | `guava_field(spec)` helper (tier → `required` + description suffix). `start_story` builds the core checklist from `intake.CORE`. `on_story_complete` → `start_details(call, module)` or qualify. `on_task_complete` for each details task → the existing qualify logic, moved into `run_qualify(call)`. `on_session_end` writes the record to `Application/intake_records/{call_id}.json` |
| `Application/qualification.py` | the new flags (§1.6); `QUALIFY_FIELDS` grows |
| `Application/compliance.py` | no new verbatim lines. Stage 6's documents Todo adds "and a short form for details like insurance policies and your doctors' contact information" |
| `Documents/.../MVP Flow Design.md` | Part 3 graph (§2.1), the Stage 4 description, and a link to this doc |

### 2.3 Conversation config (the "meat and potatoes")

**Story task checklist:**
1. Todo: thank them for their patience; invite them to tell what happened in their own words, at their own pace. If they sound upset, let them know they can take their time.
2. `narrative` field: let them finish; acknowledge injuries with care; mirror their words ("the crash", not "the collision").
3. Todo: thank them; explain you have a few questions to make sure the attorney has the full picture; for anything they already said, briefly confirm it instead of asking again.
4. The remaining core fields, in checklist order: critical first, then important.

**Details task checklist** (per module): the module's fields, critical first. Then the closing Todo: "Briefly recap what happened, their injuries, and their treatment in a sentence or two, and ask if anything needs correcting."

**Objective wording (both tasks):**
- Gather facts only.
- Ask neutrally about what each person was doing.
- Never comment on fault, case strength, coverage or deadlines, or what an answer means for the case.
- Never ask for a Social Security number, policy numbers, or bills; those come later on a form.

The last point is enforced by **not having those fields**. If the caller volunteers them, `on_question` / persona guidance says the form will cover it.

### 2.4 Tests

- **Offline:**
  - schema integrity: unique keys, valid tiers, critical mc fields include `not_sure` where meaningful;
  - the `guava_field` mapping;
  - routing for each `incident_type` (MockCall);
  - `completeness` and `build_record` with missing / unknown values;
  - the new flags;
  - the existing story/re-check/next-steps tests still pass after the qualify move.
- **Live roleplays** (mock_api in-process, as today):
  1. MVA happy path (rear-end, ER, knows their insurer). Pass:
     - reaches next steps;
     - doesn't re-ask volunteered facts;
     - asks the seat belt neutrally;
     - recaps.

     Fail:
     - asks for the SSN or policy numbers;
     - comments on fault or value.
  2. Commercial truck, caller on the job → `commercial_vehicle` and `on_the_job` flags; the employer goes through the conflict re-check.
  3. "I don't know" caller (no insurer, unsure about UM, witnesses or report) → accepted once, not re-asked; reaches next steps; `important_missing` is populated.
  4. Slip-and-fall stub → `details_premises` → next steps with `non_mva_case_type`.
  5. Med-mal stub → `details_medical` → `route_nurse_intake`.
- The user phone-tests the MVA path end to end.

### 2.5 Out of scope (this phase)
- Sending the questionnaire.
- E-sign / SMS.
- CRM persistence beyond the local JSON.
- A full premises / med-mal / wrongful-death intake.
- LLM-written summaries: the record is assembled by code from fields.
- Asking DOB, health insurance or Medicare.

---

## Summary

- **What the research says:** there's no single industry form. Every firm runs an intake sheet whose fields cluster around the four things the attorney decides on: liability, damages, coverage and time. Everything deeper goes on a post-signing questionnaire.
- **What we build:** two documents.
  - An **intake sheet**: a common core plus a case-type module. Motor vehicle is full; slip-and-fall and med-mal are stubs.
  - An **intake record** for attorney review: the sheet grouped by decision driver, plus flags, a completeness audit, and the list of what's deferred to the questionnaire.
- **One schema drives both.** Each field has a tier:
  - **critical:** required; "unsure" is acceptable;
  - **important:** asked once.

  The tier sets the Guava `required` flag and the field description, and it defines "done": every critical field answered (even "unsure"), every important field asked once. A third "opportunistic" tier (record only if volunteered) was dropped after live testing: Guava has no way to resolve a field it may never ask about. Volunteered details live in the narrative instead (§1.1, live finding 2).
- **The conversation:** a funnel. Narrative first, in the caller's words; then only the gaps, asked neutrally; then a short recap. Never fault, value, coverage or deadline commentary, and never SSN, policy numbers or bills.
- **The graph:** Story (narrative + core) branches in code on `incident_type` to a module Details task, then the existing qualify → NextSteps. If live tests show the split causes re-asking, we fall back to one task with the module's fields chosen in code.
