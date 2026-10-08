# Personal Injury Intake: Case-Details Research (Story stage)

Scope: what a PI intake specialist collects about the case once the caller has passed triage and conflicts, which documents that information goes into, and how specialists ask for it. The focus is Florida motor-vehicle accidents (MVA), with short notes for slip-and-fall and medical/nursing-home cases. This builds on `Research Findings.md` (RF), which already covers the role, conflicts, the retainer and the Florida ethics rules; RF sections are cited instead of repeated.

Confidence levels: **High** (statute, or several independent sources agree), **Medium** (one practitioner or first-party source, or several vendor sources agree), **Low** (vendor marketing, or my own inference).

---

## Key takeaways

1. **No industry-standard form exists.** Every firm uses its own intake sheet, usually inside its case-management software (Litify, Filevine, CASEpeer, SmartAdvocate, Clio). Vendors don't publish their field lists (Filevine, Litify and SmartAdvocate were checked). The "standard" is the set of fields that recurs across firm forms, practitioner checklists and vendor templates. Section 2 lays them out. **High**.
2. **Intake produces two documents and feeds a third.** (a) The **intake sheet**: structured fields, filled during the call. (b) The **intake summary** for the reviewing attorney: a short narrative plus red flags. (c) The **client questionnaire**: the long form the client fills in *after* signing, with full insurance details, every provider, bills, wages and prior history. The phone call covers (a) and (b) only. **Medium-High**.
3. **Practitioners say outright that the first call should be shortened.** Miller & Zois: the sheet is cut down for recent injuries when the person "is in acute pain and the firm only needs to decide whether a potential case exists." CASEpeer: "requesting too many details at intake can burden your prospective clients," so the detailed form is sent later. **Medium-High**.
4. **What the attorney's accept/decline decision depends on** comes down to four things: **liability** (how it happened and what proves it), **damages** (injury severity and treatment), **coverage** (whose insurance pays, and UM/UIM in auto cases), and **time** (the statute-of-limitations inputs). Every on-call field should serve one of these, or conflicts, or routing. **High** (Pierson 2024; RF 1.5).
5. **Florida MVA specifics change what's worth asking:**
   - **PIP 14-day / emergency medical condition:** caps benefits at $2,500 without an EMC (RF 1.5).
   - **Permanent-injury threshold for pain-and-suffering damages:** Fla. Stat. 627.737(2).
   - **The >50% comparative-fault bar:** Fla. Stat. 768.81(6).
   - **Seat-belt use:** may be considered as comparative negligence, Fla. Stat. 316.614(10).
   - **Crash reports:** confidential for 60 days, but available to the parties, Fla. Stat. 316.066.

   **High** (statutes).
6. **UM/UIM coverage is the highest-value insurance question** in auto cases: it "must be determined immediately," and it often caps a significant case's value (Pierson 2024). Most callers won't know their limits on the phone. Ask *whether* they have it, and leave the amounts for the questionnaire. **Medium**.
7. **Interview technique is "funnel":** an open narrative first, then narrower questions, then closed confirmations. Mirror the caller's own words, don't use leading questions, and expect trauma-related gaps in memory. **Medium** (general legal-interviewing sources; none specific to PI).
8. **Don't collect on the call:** the full SSN, full medical history, bills or amounts, policy numbers, or anything framed as a fault judgment. These belong to the post-signing questionnaire or to the attorney. **Medium**.

---

## 1. The documents

| Document | Who fills it | When | Purpose | Confidence |
|---|---|---|---|---|
| **Intake sheet / lead record** | Intake specialist, live on the call | First call | Structured facts for the accept/decline decision, conflicts and routing. Lives in the CRM. | Medium-High (M&Z sheet, CASEpeer, Litify, RF 2.1) |
| **Intake summary / memo** | Intake specialist (or software), right after the call | End of the first call | One-paragraph overview, plus red flags and missing information, for the reviewing attorney | Medium (RF 2.2; CaseMark "case foundation document"; no public M&M template) |
| **MVA supplement questionnaire** | The client, in writing | After signing | Deep auto detail: scene conditions, statements given, photos, vehicle ownership and finance, full coverage breakdown for the caller **and resident relatives** | High that it exists (JZ helps, a Florida firm) |
| **Client questionnaire** | The client, in writing | After signing, or before the consultation | Every provider (address, dates, bills), employer and wages, prior accidents and claims, health insurance, Medicare/Medicaid | High (LucasLaw, CASEpeer, Pierson's "New Client Questionnaire") |
| **Signing packet** | Client signs | At or after signing | Retainer, Statement of Client's Rights, HIPAA and medical authorisations, letter of representation, list of providers, CMS Medicare forms | High (Pierson's list; RF 2.4–2.6) |

**Implication:** the Story task produces the **intake sheet** and the **intake summary**. The other three documents are where the deferred fields go. The agent can tell the caller "the team will send you a short form for the details like policy numbers and your doctors' contact info," which is what firms actually do.

---

## 2. Field crosswalk: what recurs across intake forms

Sources:
- **MZ:** Miller & Zois PI intake sheet (Maryland auto).
- **LL:** LucasLaw PI client questionnaire (Illinois).
- **JZ:** JZ helps MVA supplement (Coral Gables, FL).
- **CP:** CASEpeer intake guide.
- **DP:** Daniel Pierson, "Initial intake: A checklist of factors to consider," *Plaintiff Magazine*, Oct 2024.
- **MM:** Morgan & Morgan web form and first-call description (RF 2.1).
- **V:** other vendor templates (Smartsheet, Clio auto, WEBRIS, Knabe).

**When** is when the field gets collected:
- **Call:** on the first call.
- **Post:** after signing, by questionnaire.
- **Firm:** the firm obtains it itself, e.g. by ordering the crash report or requesting the policy limits.

### 2.1 Common core (every case type)

| Field | Sources | When | Notes |
|---|---|---|---|
| Caller's name and contact; preferred contact method | MZ, LL, CP, MM | Call | CASEpeer: get contact details and preferred method "right away". Already collected in our Opening and Conflict stages. |
| Date of incident | MZ, LL, JZ, CP, MM | Call | Drives the statute of limitations. Already collected in ConflictScreen. |
| Time of day | MZ, LL, JZ | Call (optional) | Low value on the phone; it's in the crash report. |
| Location (city/county, street or intersection) | MZ, LL, JZ, MM ("Venue", ZIP) | Call | Needed for venue and jurisdiction, and to identify the police agency. |
| Case type | LL, MM, V | Call | Selects the module. |
| Narrative: how it happened | MZ, LL ("be very specific"), JZ, CP, DP, MM | Call | The single most important field. CP: get it "as soon as possible", since memory fades. |
| Defendants / other parties | LL, MZ, MM | Call | Feeds the conflict re-check. |
| Government entity involved | LL ("Is any Defendant a Municipality"), DP | Call | Special notice rules apply (RF takeaway 6); governments "rarely, if ever, settle without litigation" (DP). |
| Police / incident report: made? agency? report number | MZ, LL, JZ | Call: made + agency. Number optional. Firm: the report itself | Callers often have the exchange-of-information form, not the number. |
| Witnesses: any? names | MZ, LL, CP, DP | Call: yes/no. Post: contact details | CP: "Witnesses can make or break a case." |
| Photos / video exist (scene, vehicles, injuries) | LL, JZ, DP, V | Call: yes/no | Ask who holds them. Uploading is a post-call step. |
| Injuries (body parts, symptoms) | MZ, LL, CP, V | Call | In the caller's words. Don't press for diagnoses. |
| Treatment so far (ER, ambulance, doctor, imaging, therapy) | MZ, LL, V | Call: type + first date. Post: every provider | Florida PIP makes the first-treatment date critical (Section 3). |
| Still treating / future appointments | LL, MZ | Call | A treatment gap is a value and causation problem ("treatment gaps... give opposing adjusters grounds to dispute causation"). |
| Time missed from work | MZ, LL, CP | Call: yes/no + employed? Post: employer and wages | |
| Impact on daily life | MZ, CP | Call (optional) | Often volunteered in the narrative. |
| Statements given to / contact from the other side's insurer | LL, JZ, DP | Call | Flags a recorded statement or signed papers. The attorney wants to know at once. |
| Prior representation / hired an attorney | MM, V, RF 1.5 | Call | Already in ConflictScreen (`represented`). |
| Prior accidents, claims or lawsuits; injuries to the same body part | LL, DP, MZ | Call: one yes/no. Post: details | DP: undisclosed prior claims "can be devastating". One gentle question on the call, no deep history. |
| Health insurance; Medicare/Medicaid | LL, V (lien checklists) | Post | Lien handling. Not decision-relevant on the call. |
| Date of birth | MZ, LL | Post (or the firm's choice) | Identity and Medicare. Not needed for the decision. |
| SSN (last 4 or full) | MZ, LL | **Never on this call** | Sensitive. A recorded AI call is the wrong channel. |
| Referral / marketing source | LL, MM, RF 1.6 | Call (optional) | A firm KPI. Low priority for the MVP. |

### 2.2 Motor-vehicle module

| Field | Sources | When | Notes |
|---|---|---|---|
| Caller's role: driver / passenger / pedestrian / cyclist / motorcyclist | V (seat position), MZ | Call | Already in the current Story fields. Decides whose PIP applies, and the motorcyclist PIP exclusion. |
| Number of vehicles | V | Call (optional) | Usually clear from the narrative. |
| Type of collision (rear-end, intersection, etc.) | V, DP | Call: from the narrative | DP: a rear-end collision is the easiest liability call. Don't ask it as a separate question. |
| Other driver's name | MZ, LL ("Defendants") | Call | Already collected as `adverse_parties`. |
| Other driver's insurer | MZ, CP, V | Call (optional) | Callers often know it from the exchange form. The policy number goes to the firm. |
| Other vehicle commercial / work truck / rideshare | V, rideshare sources | Call | Opens additional coverage and defendants. Feeds the conflict re-check (e.g. the employer). |
| Caller's own auto insurer | LL, JZ, MZ, CP | Call | Their PIP carrier. |
| Caller has PIP / UM / MedPay | JZ, LL, DP | Call: UM yes/no/unsure. Post: limits | DP: UIM "must be determined immediately". Callers rarely know limits. |
| Resident relatives' auto insurance | JZ | Post | A Florida PIP/UM nuance. Questionnaire only. |
| Claim number(s) opened | JZ, LL | Post | |
| Seat belt worn | V (Smartsheet) | Call | Florida: may be considered as comparative negligence (316.614(10)). Ask neutrally. |
| Airbags deployed / vehicle drivable / towed | V, 316.066 | Call (optional) | Proxies for severity. Towing also triggers a long-form crash report. |
| Ambulance from the scene | LL (treatment list), JZ ("How did you leave the scene") | Call | Severity, and supports an EMC. |
| Told at the ER / by a doctor it was an emergency | Florida PIP sources | **Not on the call** | A medical determination the caller can't reliably report. The firm gets it from records. |
| Property damage to the vehicle | MZ, CP | Call (optional) | Low impact on the decision. |
| Red-light camera / dashcam / OnStar | JZ | Post | Evidence preservation. The firm acts on it. |
| Hit-and-run (other driver unidentified) | Search results (general practice) | Call: from the narrative | Recovery then depends on UM. |
| On the job at the time | Rideshare and WC sources | Call | Workers' comp overlap. Flag for the attorney. |
| Rideshare app status (if a rideshare driver was involved) | Nolo, rideshare firms | Call: only if rideshare | Coverage depends on app status. |

### 2.3 Slip-and-fall module (stub)

Florida business premises: the claimant must prove the business had actual or constructive knowledge of a "transitory foreign substance" (Fla. Stat. 768.0755). **High**. The fields that track that:
- the type of property (business / residence / government);
- what caused the fall;
- whether staff were told, and whether an incident report was made;
- photos;
- witnesses;
- whether anyone knew how long the hazard had been there.

These are the minimum stub fields. The full premises questionnaire is a later phase.

### 2.4 Medical malpractice / nursing home module (stub)

M&M routes these to RN screeners (RF 1.1 #7). Florida medical malpractice limitation: 2 years from the incident or its discovery, never more than 4 years (Fla. Stat. 95.11(5)(c)). **High**. Stub fields:
- the provider or facility name;
- the approximate date of the care;
- when the caller realised something was wrong (the discovery date);
- the harm.

The case then routes via the `route_nurse_intake` flag. No further medical questioning by the agent.

### 2.5 Wrongful death

Wrongful death has its own limitation period (Fla. Stat. 95.11(5)(e)), and in Florida the claim is brought by the estate's personal representative. Our triage already routes calls about someone else away (`routed_third_party`), so this is out of the Story stage's scope. Noted for the record.

---

## 3. Florida hooks behind specific questions (MVA)

| Rule | What it means for intake | Source / confidence |
|---|---|---|
| PIP: initial care within 14 days; $10k, or $2.5k without an emergency medical condition | Ask the first-treatment date and type (ER vs. doctor). Never tell the caller what it means. | Fla. Stat. 627.736(1)(a) — High (RF 1.5) |
| Permanent-injury threshold for pain-and-suffering damages | The attorney needs severity signals: fractures, surgery, imaging, ongoing treatment, scarring. Intake captures them; it does not assess permanency (that's a physician's opinion). | Fla. Stat. 627.737(2) — High |
| Modified comparative fault: >50% at fault → no recovery (not medical negligence) | Capture **what the other party did** and **what the caller was doing**, in neutral terms. Never ask "was it your fault?" | Fla. Stat. 768.81(6) — High (RF 1.5) |
| Seat-belt non-use may be considered as comparative negligence | Ask "Were you wearing your seat belt?" plainly, with no commentary. | Fla. Stat. 316.614(10) — High |
| Long-form crash report required for injury or complaints of pain, a towed vehicle, or a commercial vehicle; confidential 60 days but available to the parties and their lawyers | Ask whether police came and which agency. The firm obtains the report. | Fla. Stat. 316.066 — High |
| Limitation 2 years (after 3/24/2023) / 4 years | Already computed in `qualification.py` from `incident_date`. | Fla. Stat. 95.11 — High (RF 4.1) |
| Government defendant: written pre-suit notice | Already captured as `government_involved`. | RF takeaway 6 — High |
| UM is optional but must be offered; a rejection must be in writing | Ask whether they have UM. Rejection forms are a questionnaire item. | Fla. Stat. 627.727 — Medium (firm blogs; statute not re-fetched) |

---

## 4. How specialists ask: interview technique

- **Funnel:** open narrative → targeted gaps → closed confirmations. "A typical sequence may start with an open question to establish context, then use funnel questioning to focus on details, and finally closed questions for confirmation." **Medium**. This is the structure the Story task already uses.
- **Narrative first, details later:** gather the overall story first. Avoid granular trauma details in the first pass, and build a timeline ("What happened next?"). (Tahirih Justice Center.) **Medium**.
- **Mirror the caller's language** rather than imposing legal labels (ABA trauma-informed intake). For example, say "the crash" if they say "the crash", not "the collision event". **Medium**.
- **Check in:** offer a pause if the caller is distressed, and don't assume they're ready for full detail (ABA). **Medium**.
- **Neutral, non-leading questions:** "What was the other driver doing?" or "Where were you headed?" rather than "He ran the light, right?" **Medium**.
- **Expect memory gaps:** "the most painful moments are hardest to clearly remember." Treat gaps as normal, not as inconsistency. Record "unsure" rather than pressing. **Medium**.
- **Recap:** summarise the key points back to the caller to confirm and invite corrections, then explain next steps. **Medium**.
- **Facts only, no evaluation:** "staff do not tell the caller whether they have a case"; no outcome, settlement or timeline promises. **High** (consistent with Op. 88-6 and Rule 4-7.13; RF 4.x).
- **Customary advice intake does give** (process, not legal advice): keep all photos and documents, keep up with medical treatment, and don't post about the accident on social media (DP's instruction to new clients). The firm decides whether intake or the attorney says this. Our NextSteps already covers "gather photos, the police report number…". **Medium**.

---

## 5. Prioritisation for a phone intake

Tiers follow the four decision drivers (takeaway 4). "Collected" means the field has a value **or** the caller explicitly doesn't know or it doesn't apply.

| Tier | Meaning | MVA fields |
|---|---|---|
| **Critical** | The attorney can't decide without it | narrative, incident type, incident state + location, caller's role, injuries, treatment type + first date, police came, other vehicle commercial/work/rideshare, caller on the job, government involved, other parties named |
| **Important** | Shapes value or coverage; ask if not volunteered | seat belt, ambulance from scene, still treating, missed work, the other side's insurer, caller's own insurer, UM yes/no, witnesses, photos, statement to the other insurer, prior injury to the same body parts |
| **Opportunistic** | Record if volunteered, otherwise skip | time of day, number of vehicles, airbags, vehicle towed or drivable, property damage, daily-life impact, police report number |
| **Deferred** | Not on this call | policy numbers and limits, claim numbers, provider list and bills, employer and wages, health insurance, Medicare/Medicaid, DOB, SSN, resident relatives' policies, camera/OnStar evidence |

**Completion rule (the "enough" judgement, made concrete):** the stage is complete when every **critical** field is collected (a value, or unknown / not applicable), and every **important** field is collected, volunteered, or was asked once. The caller may decline or not know anything; "unsure" is a valid answer and is never re-asked.

**Call-length guard:** practitioners shorten intake when the caller is in acute pain (MZ). If the caller is struggling, the important tier can be skipped and flagged `intake_shortened` for a follow-up call. This is an inference from MZ, not a documented rule. **Low-Medium**.

---

## 6. Implications for the agent

- **Must:**
  - get the narrative first and let the caller finish;
  - fill fields from the narrative;
  - ask only the gaps, critical tier first, one question at a time;
  - ask fault-related questions neutrally;
  - accept "I don't know" once;
  - read back a brief recap before moving on;
  - tell the caller the remaining details (policies, doctors, bills) will come in a short form after the call.
- **Must not:**
  - ask for the SSN;
  - take a full medical history or ask for bills or amounts;
  - interpret what an answer means for the case (no "that's good for your case", "PIP will cover that", or "because you weren't wearing a seat belt…");
  - tell the caller about the 14-day rule or any deadline (RF takeaway 11).
- **Produce:** a structured intake sheet (fields + tier coverage) and an intake summary (narrative recap + flags + missing fields) for the attorney.

---

## Open questions

- Whether intake should give the "don't post on social media / keep treating" advice, or leave it to the attorney: firms differ. **Recommendation:** leave it out of the MVP. NextSteps already covers gathering documents.
- Whether to ask DOB on the call (identity and Medicare): firm preference. **Recommendation:** defer.
- Exact UM statute wording (627.727) wasn't re-fetched. The intake question (UM yes/no) doesn't depend on it.
- No public Morgan & Morgan intake sheet beyond the web form (RF 2.1). The crosswalk is built from other firms' forms.

---

## Sources

### Primary (Florida statutes)
- Fla. Stat. 627.737 (tort exemption; permanent-injury threshold): https://www.flsenate.gov/Laws/Statutes/2025/627.737
- Fla. Stat. 316.614 (safety belt; comparative negligence): https://www.flsenate.gov/Laws/Statutes/2025/316.614
- Fla. Stat. 316.066 (crash reports; confidentiality): https://www.flsenate.gov/Laws/Statutes/2025/316.066
- Fla. Stat. 768.0755 (premises; transitory foreign substances): https://www.flsenate.gov/Laws/Statutes/2025/768.0755
- Fla. Stat. 95.11 (limitations; medical malpractice (5)(c), wrongful death (5)(e)): https://www.flsenate.gov/Laws/Statutes/2025/95.11
- Fla. Stat. 627.736, 768.81 (cited via RF)

### Practitioner and firm forms
- Daniel Pierson, "Initial intake: A checklist of factors to consider," *Plaintiff Magazine*, Oct 2024: https://plaintiffmagazine.com/recent-issues/item/initial-intake-a-checklist-of-factors-to-consider
- Miller & Zois, Personal Injury Intake Sheet: https://www.millerandzois.com/professional-attorney-information-center/forms-and-letters-for-personal-injury-lawyers/personal-injury-intake/
- LucasLaw, Personal Injury Client Questionnaire (PDF, read locally): https://www.lucaslaw.com/images/client-forms/LucasLaw-Personal-Injury-Client-Questionnaire.pdf
- JZ helps (Coral Gables, FL), Information Questionnaire – Motor Vehicle Accident (PDF, read locally): https://www.justinziegler.net/wp-content/uploads/2015/03/WEBSITE-ONLY-SUPPLEMENT-Information-Questionnaire-–-Motor-Vehicle-Accident.pdf

### Vendor (Medium/Low)
- CASEpeer, "Information PI firms should collect during intake": https://casepeer.com/information-personal-injury-law-firms-should-collect-during-intake
- CASEpeer, PI client intake form: https://www.casepeer.com/blog/personal-injury-client-intake-form
- Smartsheet injury intake form: https://app.smartsheet.com/b/form/2fc4b0ef05784e38af796ee4c5d6c300
- Clio, Personal Injury Intake (Auto) template (HTTP 403; seen via search summary only): https://www.clio.com/legal-templates/personal-injury-intake-auto__GEATT24005/
- WEBRIS PI intake template: https://webris.org/wp-content/uploads/2024/08/WEBRIS-__-Personal-Injury-Intake-Form-Template.pdf
- Ezel lien investigation checklist: https://ezel.ai/templates/lien-investigation-checklist/
- CaseMark intake summary workflow: https://casemark.com/workflows/client-intake-summary-questionnaire

### Interviewing technique (general legal, not PI-specific)
- ABA, "5 questions: trauma-informed intake": https://www.americanbar.org/groups/domestic_violence/Initiatives/five-for-five/5-questions-trauma-informed-intake/
- Tahirih Justice Center, "Trauma and Client Interviewing Tips": https://www.tahirih.org/wp-content/uploads/2015/07/Trauma-and-Client-Interviewing-Tips.pdf
- SQE2 questioning techniques: https://pastpaperhero.com/resources/sqe2-interview-preparation-and-conduct-questioning-techniques-and-listening-skills

### Rideshare / coverage (secondary)
- Nolo, injured in an Uber or Lyft: https://nolo.com/legal-encyclopedia/i-was-injured-while-riding-in-an-uber-or-lyft-vehicle.html
- Shiner Law Group, PIP / BI / UM explained: https://shinerlawgroup.com/auto-insurance-what-is-pip-bi-um-and-gap
