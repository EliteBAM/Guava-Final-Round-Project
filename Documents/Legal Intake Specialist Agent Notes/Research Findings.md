# Legal Intake Specialist (Personal Injury) — Domain Research Findings

**Date:** 2026-10-07
**Target firm:** Morgan & Morgan, P.A. (HQ Orlando, FL) | **Target state:** Florida

**Scope.** This document covers the domain only: the human job of a personal-injury (PI) legal intake specialist, the records that come out of an intake call, how a lead is handed to an attorney, and the Florida legal and ethics rules that limit what intake may do or say. It covers US PI practice in general, with Florida and Morgan & Morgan details wherever they differ or are documented. It deliberately leaves out voice AI, any SDK or API, e-signature vendor integration and all other implementation detail. Primary sources were used wherever possible: the Florida Statutes, the Rules Regulating The Florida Bar (the October 1, 2026 edition of Chapter 4, read in full text), Florida Bar ethics opinions, enrolled bill text, and Morgan & Morgan's own website and current job postings. Day-to-day practice facts that have no official source are labelled as first-party vendor material or as secondary sources.

**Confidence labels:** **High** = primary source, verified in the text itself. **Medium** = first-party or practice source, or several secondary sources that agree. **Low** = one secondary source, or an inference.

**How the sources were read:** Statutes and some web pages were read through a page-summarising fetch tool. Where this document puts text in quotation marks, it came from the full primary text that was downloaded and read: the Chapter 4 rules PDF, the HB 837 enrolled PDF, Opinions 24-1 and 88-6, and the MLM guide. Other quotations are short phrases as the tool returned them from the official page.

---

## Key takeaways

1. **In Florida, a non-lawyer intake interviewer has three firm limits.** Under Florida Ethics Opinion 88-6, which Opinion 24-1 applies to AI chatbots, the intake interviewer must (1) clearly identify their nonlawyer status, (2) ask only for facts, and (3) give no legal advice about the case *or about the fee agreement*. Questions about how strong the case is, what the law says, or what the agreement means must go to a lawyer. (High)
2. **An AI intake agent must say that it is AI.** Florida Bar Ethics Opinion 24-1 (Jan. 19, 2024) states that "a lawyer must inform prospective clients that they are communicating with an AI program and not with a lawyer or law firm employee". It warns against an "overly welcoming" chatbot that might give legal advice or fail to identify itself right away. It also recommends screening questions for callers who already have a lawyer. (High; the opinion is advisory, not binding.)
3. **Confidentiality starts at the first call.** Under Rule 4-1.18, what a prospective client says is confidential even if the firm never takes the case, and it can disqualify the firm from acting against that person. The rule's comment says to collect only what is "reasonably necessary" to decide on conflicts and fit. This argues for an early, minimal conflict screen (names of the parties) before collecting a detailed narrative. (High)
4. **Florida's contingency-fee rules are unusually prescriptive.** For PI cases, Rule 4-1.5(f)(4) requires a written contract signed by the client and a lawyer. It must contain exact wording confirming that the client received and signed the *Statement of Client's Rights*, and exact wording giving a 3-business-day cancellation right. The rule sets schedule caps (33⅓% / 40% / 30% / 20% and so on) and requires the Statement, signed by both client and lawyer, to be provided *before* the contract is signed. (High)
5. **The negligence limitation period is now 2 years.** HB 837 (ch. 2023-15) moved general negligence from 4 years to 2 years for causes of action accruing after March 24, 2023, the date it became law. It is now Fla. Stat. 95.11(5)(a). Claims that accrued on or before that date keep the 4-year period, so the last of them run out around March 2027. The **incident date** is therefore a field intake must capture. (High)
6. **Other Florida case-screening facts intake should know.** Under HB 837's modified comparative fault, a claimant found more than 50% at fault recovers nothing (except in medical negligence cases). PIP medical benefits require initial treatment **within 14 days** of a car accident. Claims against the government need written pre-suit notice within 3 years. Medical malpractice and wrongful death have their own rules. (High)
7. **Florida requires every party's consent to record a call.** Fla. Stat. 934.03(2)(d) allows interception only when "all of the parties to the communication have given prior consent", and an unlawful interception is a third-degree felony. A recorded intake call therefore needs consent from every party at the start. Federal law alone would only require one party's consent. (High)
8. **Intake at Morgan & Morgan is a dedicated, high-volume call-centre function, not the receptionist.** The firm's "Case Control Center" employs Case Consultants and Case Intake Specialists (CSRs). They take inbound and outbound calls, assess eligibility, enter case data, schedule callbacks, and "distribute and collect signed retainer agreements via email and text". Intake *Attorneys* make real-time acceptance decisions and chase unsigned retainers. Registered nurses screen medical malpractice and nursing-home claims. (Medium-High; first-party job postings.)
9. **Morgan & Morgan's public promise to callers.** After someone submits a form, the firm confirms by email or text, calls within 24 hours, asks what happened, where and when, and who was involved, e-mails documents for signature if it can help, and typically assigns an attorney and team within a week. The website advertises "The Fee Is Free" and 24/7 contact. (Medium-High; first-party.)
10. **Speed of response and conversion are the core measures.** Vendor and practice sources track conversion %, "want %", turn-down rate, referral rate, cost per signed case, and source ROI. Clio's 2024 secret-shopper study found that only about 40% of firms answered the phone. (Medium for the metrics, Low-Medium for the statistics.)
11. **Declined leads need a written non-engagement letter.** Malpractice-insurer guidance says to put every declination in writing: no attorney-client relationship, no opinion on the merits, a warning that time limits apply (without calculating the deadline), and a recommendation to see another lawyer promptly. The declined person also goes into the conflict system. (Medium)
12. **Litify came out of Morgan & Morgan, and the firm uses it.** Litify was founded in 2016 by people from Morgan & Morgan, and Morgan & Morgan uses it firm-wide. Its own Intake Attorney posting lists Salesforce or Litify experience as preferred. (Medium; no first-party Litify or Morgan & Morgan page states the origin directly.)

---

## Section 1 — The intake specialist role and duties

### 1.1 Core duties (US PI, with Morgan & Morgan specifics)

| # | Duty | Evidence | Confidence |
|---|---|---|---|
| 1 | First point of contact for prospective clients, on inbound and outbound calls | M&M Case Consultant (Longwood, FL): "Initial point of contact for prospective clients calling the firm"; "Manage inbound and outbound calls" — https://job-boards.greenhouse.io/morganmorganjobsapplynow/jobs/6146478004 | Medium-High (first-party) |
| 2 | Hold a consultation to judge whether the firm can help (eligibility) | M&M Case Intake Specialist – CSR: "Conduct consultations with potential clients to assess case eligibility" — https://job-boards.greenhouse.io/morganmorganjobsapplynow/jobs/6147389004 | Medium-High |
| 3 | Record the facts of the case accurately in the intake system | Same two M&M postings ("Document case information accurately"; "Collect and input prospective case data") | Medium-High |
| 4 | Schedule appointments and callbacks | Same two M&M postings | Medium-High |
| 5 | Send and collect the signed retainer (fee agreement) by email or text | M&M Case Consultant: "Distribute and collect signed retainer agreements via email and text"; CSR: "Send and obtain signed retainers via email or text" | Medium-High |
| 6 | Resolve client concerns professionally and with empathy (callers are often traumatised) | Both M&M postings; Nurse Intake posting | Medium-High |
| 7 | Specialist screening for medical malpractice and nursing-home claims by registered nurses | M&M Nurse Intake Specialist: "Vet and assess medical malpractice and nursing home claims"; requires an active RN licence — https://job-boards.greenhouse.io/morganmorganjobsapplynow/jobs/6218169004 | Medium-High |
| 8 | Track each priority PNC from first contact to signed; audit follow-up; enter dispositions in Salesforce after every meaningful contact; escalate stalled sign-ups the same day | Thomas J. Henry Law (large Texas PI firm), "PNC Intake Auditor & Sign-Up Coordinator" — https://www.jobtarget.com/jobs/jt-cxjbxb46u3/pnc-intake-auditor-and-sign-up-coordinator-austin-texas | Medium (first-party, another firm) |
| 9 | Qualify by severity, liability, treatment, statute urgency and prior representation | Lawmatics (intake CRM vendor) describes its PI qualification as scoring "severity, liability, treatment, and statute urgency" and checking "prior representation" — https://www.lawmatics.com/practice-areas/personal-injury-law/ | Medium (first-party vendor) |
| 10 | Route non-prospect calls (existing clients, adjusters, medical providers) to the right person | PI intake job listings found by search mention answering calls "from medical providers, insurance adjusters, and existing clients" and routing them. The original postings could not be opened (expired). | Low |
| 11 | In smaller firms, combine reception (greeting visitors, multi-line phones, voicemail) with intake screening and lead follow-up | Garza Law Firm (TN) "Intake/Reception Specialist" posting — https://recruiting.paylocity.com/Recruiting/Jobs/Details/4368879 | Medium (single first-party example) |

### 1.2 Organisational context

- **Morgan & Morgan runs a dedicated intake department called the "Case Control Center".** Postings place it in Longwood, FL (Orlando area) and Las Vegas, NV. The Case Consultant posting says it operates "7 days a week from 8:00 AM to 9:00 PM". The Las Vegas CSR posting gives 7:00 AM–9:00 PM PST with full weekend availability. Pay is $18/hour plus a $250 sign-on bonus after 90 days, and there is a six-week mandatory training programme. The Intake Attorney posting calls the Case Control Center "a department at the center of our nationwide growth." Sources: the M&M postings above and https://job-boards.greenhouse.io/morganmorganjobsapplynow/jobs/6150043004 — **Medium-High**.
- **24/7 contact versus staffed hours.** The M&M FAQ says "Contact us 24/7". The homepage lists (877) 667-4265, presented as available 24/7 (https://www.forthepeople.com/faq/, https://www.forthepeople.com/). The intake postings, however, give staffed hours of 7 or 8 AM to 9 PM. How after-hours calls are handled is **not documented**; see Open Questions. **Medium**.
- **Several advertised numbers.** M&M's homepage shows (877) 667-4265, and its "process" blog post shows 877-454-0415 (https://www.forthepeople.com/blog/what-morgan-morgans-process/). This fits the industry practice of using tracking numbers per page or campaign, but that is an inference. **Low**.
- **Tracking numbers per campaign are standard practice.** CallRail, a call-tracking vendor, markets tracking numbers that attribute calls to "the specific ad, campaign, or keyword". Lawmatics and Litify both describe linking calls to marketing source (CallRail integration) and measuring "Leads per source, Cost per lead, Cost per case, ROI per source." Sources: https://www.lawmatics.com/practice-areas/personal-injury-law/, https://www.litify.com/blog/how-leading-plaintiff-firms-use-litify-to-optimize-marketing-and-intakes, CallRail law-firm guide https://cdn.mediavalet.com/usva/callrail/36h_F7RHw0iJWPNWFIn9VQ/RdTHaxHkVU6EJLoR5fWXew/Original/Call%20Tracking%20101%20for%20Law%20Firms-CallRail%20%281%29.pdf (seen in search results, not opened) — **Medium**.
- **Scale at Morgan & Morgan.** Wikipedia (secondary) says the firm received "over two million phone calls and signed up 500 new cases each day" in 2018, and reports 1,000+ attorneys and about 140 offices in 2025. A Litify case study quotes M&M's Matt Morgan on visibility into "our 60,000 cases". Sources: https://en.wikipedia.org/wiki/Morgan_%26_Morgan, https://www.litify.com/liticast/standardizing-attorney-performance-morgan-and-morgan/ — **Low-Medium**.
- **How intake varies by firm size** (practice pattern pieced together from postings; **Low-Medium**):
  - *Solo and small firms:* the receptionist or legal assistant often doubles as intake (see the Garza posting). Many use outsourced answering or intake services for after-hours or overflow calls.
  - *Mid-size PI firms:* dedicated intake specialists, sometimes an after-hours intake shift, and an attorney who reviews leads.
  - *Large and national firms (M&M, Thomas J. Henry):* a call-centre model with tiers (CSR or Case Consultant, then Intake Attorney), specialist screeners such as nurses, auditors and sign-up coordinators, and CRM-driven pipelines on Salesforce or Litify.
- **Outsourced intake is a mature market.** Alert Communications, a first-party vendor, advertises 24/7 legal call answering with "trained intake specialists who qualify cases", bilingual screening, retainer delivery with "Retainer sent within minutes of qualification", "multi-touch sequences" to recover unsigned retainers, and overflow staff working from "practice-specific scripts" (https://www.alertcommunications.com/). Smith.ai is described as sending prospects, clients, court staff and opposing counsel down different call paths (Lawyerist, secondary: https://lawyerist.com/news/choosing-between-ai-and-a-live-receptionist-smith-ai/). **Medium**.

### 1.3 How intake relates to other roles

| Role | Relationship to intake | Evidence / confidence |
|---|---|---|
| Receptionist | Handles general office calls and visitors. In small firms the same person may also do intake; in large firms intake is a separate department. | Garza posting; M&M postings — Medium |
| Intake attorney | Reviews materials such as police reports and photos, makes the real-time decision to accept, gives "attorney-level reassurance" before the retainer is signed, coordinates onboarding with managing partners, and follows up pending unsigned retainers. Has no litigation caseload. | M&M Intake Attorney posting (6150043004) — Medium-High |
| Case manager / pre-litigation team | Takes over after sign-up. M&M says a client "typically will be assigned an attorney and legal team within a week", and "Your lawyer will contact the other side… and inform them that Morgan & Morgan represents you." | https://www.forthepeople.com/blog/what-morgan-morgans-process/ — Medium-High |
| Paralegal | Works under lawyer supervision; Rule 4-5.3(c) makes the lawyer responsible for paralegal work product. Intake staff are also nonlawyers subject to 4-5.3. | Rules Regulating The Florida Bar, Ch. 4 — High |
| Referral and VIP intake | M&M has a "VIP Client Intake Specialist" who handles cases generated by M&M attorneys and external firms. Seen only in a search-result snippet; the posting could not be opened. | Low |

### 1.4 Types of caller and how each is typically handled

Most of this table is practice-based with little primary support. Confidence is **Low-Medium** unless a rule is cited.

| Caller type | Typical handling | Basis |
|---|---|---|
| New potential client (PNC) about their own injury | Full intake: conflict screen, facts, qualification, then attorney review, sign-up or decline | M&M postings and process page — Medium-High |
| Caller phoning for someone else (family member, or the estate in a death case) | Collect the caller's relationship and authority. The actual claimant (or the personal representative of the estate) must be the one who signs. | Practice; Rule 4-1.5(f)(2) requires the *client's* signature — Medium |
| Existing client | Route to their case team. M&M clients contact their "dedicated legal team" by "phone, email, and our client portal". | https://www.forthepeople.com/faq/ — Medium |
| Person already represented by another lawyer on this matter | Ask early. Opinion 24-1 recommends "screening questions that limit the chatbot's communications if a person is already represented by another lawyer." Rule 4-4.2's comment allows communication with a represented person "who is seeking advice from a lawyer who is not otherwise representing a client in the matter" (for example, someone seeking a second opinion or a new lawyer). Escalate to an attorney. | Opinion 24-1; Rule 4-4.2 comment — High |
| Insurance adjuster or defence counsel or opposing counsel | Not a prospect. Do not discuss client matters (Rule 4-1.6 confidentiality); take a message or route to the handling attorney. | Rule 4-1.6; practice — Medium |
| Medical provider or lien holder | Route to the case team; confidentiality applies | Practice — Low |
| Wrong practice area | M&M handles many practice areas (its form has 30+ case types), so routing within the firm is common. Otherwise decline or refer, for example to The Florida Bar Lawyer Referral Service at 800-342-8011. | https://www.forthepeople.com/; https://www.floridabar.org/public/lrs/ — Medium |
| Vendors, solicitors, spam | Screen out | Practice — Low |

### 1.5 Case qualification criteria (PI screening)

- **Liability.** Was someone else at fault? Police report, photos, witnesses. M&M Intake Attorneys review "police reports and photographs" to make real-time acceptance decisions (M&M Intake Attorney posting). A Florida-specific point: under HB 837 a claimant "greater than 50 percent at fault for his or her own harm may not recover any damages" (Fla. Stat. 768.81(6), from ch. 2023-15 enrolled text, §768.81(6); this does not apply to medical negligence). **High**.
- **Damages.** Injury severity, treatment, lost wages. Lawmatics scores "severity" and "treatment"; an expired Intake Attorney posting (Employbridge, Phoenix) lists "liability, damages, statute limitations, and jurisdictional factors" as the basis for retain or decline decisions (https://www.legal.io/jobs/5849718/Full-time/Intake-Attorney/Phoenix/Arizona). **Medium**.
- **Collectability / insurance.** Is there at-fault liability coverage, plus the caller's own PIP and UM coverage? Florida lets a claimant demand a sworn coverage disclosure, which the insurer must give "within 30 days of the written request of the claimant" (Fla. Stat. 627.4137(1)). **High** for the statute; **Medium** that intake collects insurer and claim-number details (M&M asks for "Insurance details").
- **PIP 14-day treatment rule (Florida car accidents).** PIP medical benefits require that the injured person "receives initial services and care… within 14 days after the motor vehicle accident". The limit is $10,000, reduced to $2,500 if no emergency medical condition is found (Fla. Stat. 627.736(1)(a)). Intake should capture the date of first treatment. **High**.
- **Prior representation.** Has the caller already hired or signed with another firm? Lawmatics lists "prior representation" as a qualification factor, and Opinion 24-1 recommends screening for represented persons. **High / Medium**.
- **Statute of limitations and time-sensitive notices.** See Section 4.1. **High**.
- **Jurisdiction and venue.** Where the incident happened and the caller's state or ZIP code. The M&M form collects ZIP code and "Venue". **Medium**.

### 1.6 How intake performance is measured

- Litify names the KPIs "Want percentage, Conversion percentage, Referral rate, Turn-down rate" and "Leads per source, Cost per lead, Cost per case, ROI per source." Source: https://www.litify.com/blog/how-leading-plaintiff-firms-use-litify-to-optimize-marketing-and-intakes. **Medium** (first-party vendor).
- Lawmatics stresses response speed ("Send SMS replies in minutes…") and reports linking marketing source to signed cases. **Medium**.
- Thomas J. Henry measures call quality ("professionalism, empathy, fact capture, and closing effectiveness"), uses weekly scorecards, and requires dispositions to be entered "immediately after every meaningful contact". **Medium**.
- Clio's 2024 Legal Trends Report secret-shopper study (as reported by the Illinois Supreme Court Commission on Professionalism, a secondary source): only 40% of firms answered phone calls, down from 56% in 2019; 33% replied to emails; 48% could not be reached by phone at all. Clio's own press release returned HTTP 403 and could not be checked directly. Source: https://www.2civility.org/2024-clio-legal-trends-report-fixing-the-first-impression-problem-for-law-firms/. **Low-Medium**.
- The often-quoted "contact within 5 minutes → 100× more likely" figure comes from a general sales study (MIT/InsideSales), not from legal intake. It was seen only in vendor blogs. **Low**; do not rely on it.

### 1.7 Following up on unsigned leads

- **Who does it:** M&M Intake Attorneys "Follow up on pending unsigned retainers". CSRs schedule callbacks and place outbound calls. Thomas J. Henry has an auditor who escalates "stalled sign-ups". **Medium-High**.
- **Cadence:** Vendor material describes multi-touch sequences (Alert: "Multi-touch sequences recover unsigned retainer agreements"; Lawmatics: drip email and SMS nurture). Specific schedules (for example call at 5 minutes, text, call at 2 hours, email at 24 hours, last call at 48 hours) appear only in secondary marketing blogs. **Low**.
- **When follow-up stops:** No authoritative source found. See Open Questions. From the risk-management side, MLM advises that a lead the firm will not take should be closed with a non-engagement letter rather than left open (Section 2.7).

### Implications for an AI intake specialist (Section 1)

- **Must:** answer as a dedicated intake function, not a general receptionist; identify the caller type early and route existing clients, adjusters, providers and opposing counsel away from the PNC script; collect the qualification facts (incident date, location, how it happened, injuries, treatment and date of first treatment, police report, insurance on both sides, prior or current lawyer); schedule callbacks; and record a disposition for every contact.
- **Must:** flag the triage signals that matter for this firm: high severity, an approaching limitation deadline, a government defendant, medical malpractice or nursing home (route to nurse intake), and wrongful death.
- **Must not:** make the acceptance decision. At M&M, acceptance is made by an Intake Attorney.
- **Must produce:** a structured lead record with marketing source, a disposition, and a follow-up task for unsigned leads.

---

## Section 2 — Documents and records produced from or around an intake call

### 2.1 Intake form / questionnaire / lead record

- **What it is:** the structured record of the PNC and the incident, held in the intake CRM. Litify, built on Salesforce, describes "dynamic intake questionnaires" and attorneys receiving "call recordings, form submissions, and notes all in one record". M&M Intake Attorneys "Document interactions in the intake system". **Medium**.
- **Fields M&M collects on its public web form:** First and Last Name, Phone, ZIP code, Email, Case Type (dropdown of 30+ types, e.g. Car Accident, Slip & Fall, Workers' Compensation, Medical Malpractice), Case Details (free text), plus hidden or optional fields: Marketing Sub Source, CDP Marketing Id, Venue, Street Address, City, State, Work Phone, Extra Info. The form carries TCPA-style consent wording for autodialled or prerecorded calls and texts. Source: https://www.forthepeople.com/ — **Medium-High** (first-party, read through the fetch tool).
- **What M&M asks on the first call:** "What happened?", "Where and when did it happen?", "Who was affected and involved?" It then asks for medical records, insurance details and evidence of losses. Source: https://www.forthepeople.com/blog/what-morgan-morgans-process/ — **Medium-High**.
- **Typical PI intake sections** (vendor template, CASEpeer): client contact; employment; accident details (location, weather, road conditions); other driver's name, contact, insurance and vehicle; medical information and injury description; witnesses; client's vehicle and insurance; impact on daily life; property damage; prior lawsuits and claims; signature and consent. Source: https://www.casepeer.com/blog/personal-injury-client-intake-form — **Medium**.
- **Legally required content:** none is prescribed by statute or rule. Rule 4-1.18 *limits* what should be collected before conflicts are cleared (Section 4.2). **High**.

### 2.2 Intake memo / case summary for attorney review

- **What it is:** a summary handed to the reviewing attorney (facts, liability, injuries and treatment, insurance, limitation date, red flags, recommendation). Litify describes attorneys receiving screened cases with "full context… call recordings, form submissions, and notes all in one record", and "qualification rules and approval workflows". **Medium**.
- **Legal requirement:** none specific. Opinion 88-6 requires that "the lawyer evaluate all information obtained by a nonlawyer employee during the client interview", which in practice requires a reviewable summary. **High** for the duty; **Low** for any particular memo format, as no public M&M template was found.

### 2.3 Conflict-check request / record

- **What it is:** a search of the names of the prospective client, adverse parties and insured parties against the firm's current, former and prospective client records. Clio Grow advises collecting "the information you require from them for a conflict check" in a pre-screening step *before* booking a consultation, and Clio Grow can scan contacts, notes and communications for conflicts. Lawmatics includes conflict checking in its CRM. **Medium**.
- **Why it matters legally:** Rule 4-1.18(b)–(c) and the comment ("In order to avoid acquiring disqualifying information from a prospective client, a lawyer considering whether to undertake a new matter should limit the initial consultation to only information as reasonably appears necessary for that purpose.") **High**.
- **Declined PNCs go into the conflict system too.** MLM advises: "be sure to enter information concerning the declined potential client in your conflict system." **Medium**.

### 2.4 Contingency fee agreement (Florida, Rule 4-1.5(f)) — the "retainer"

Source for everything in this subsection: Rules Regulating The Florida Bar, Chapter 4 (RRTFB Oct. 1, 2026), https://www-media.floridabar.org/uploads/2026/10/2027_04-OCT-Chapter-4-RRTFB.pdf. **High**.

- **Must be in writing and state the method of calculating the fee,** "including the percentage or percentages that will accrue to the lawyer in the event of settlement, trial, or appeal", the costs to be deducted, and "whether those costs are to be deducted before or after the contingent fee is calculated" (4-1.5(f)(1)).
- **Signatures:** the agreement must be "reduced to a written contract, signed by the client, and by a lawyer for the lawyer or for the law firm". Every participating firm must sign, and the client must receive a copy of the signed contract (4-1.5(f)(2)). An intake specialist can deliver and collect the contract but **cannot be the firm's signatory**.
- **Wording required in PI, wrongful-death and tort property-damage contracts (4-1.5(f)(4)(A)):**
  - (i) "The undersigned client has, before signing this contract, received and read the statement of client's rights and understands each of the rights set forth in it. The undersigned client has signed the statement and received a signed copy to refer to while being represented by the undersigned lawyer(s)."
  - (ii) "This contract may be cancelled by written notification to the lawyer at any time within 3 business days of the date the contract was signed, as shown below, and if cancelled the client is not obligated to pay any fees to the attorney for the work performed during that time. If the lawyer has advanced funds to others in representation of the client, the lawyer is entitled to be reimbursed for amounts that the lawyer has reasonably advanced on behalf of the client."
- **Fee schedule (4-1.5(f)(4)(B)(i)).** Fees above these levels are "presumed, unless rebutted, to be clearly excessive" without prior court approval:
  - *Before an answer is filed or arbitrators are demanded (or the time for doing so passes):* 33⅓% of any recovery up to $1M, plus 30% of $1M–$2M, plus 20% above $2M.
  - *After that point, through judgment:* 40% up to $1M, plus 30% of $1M–$2M, plus 20% above $2M.
  - *If all defendants admit liability and ask for a trial on damages only:* 33⅓% up to $1M, plus 20% of $1M–$2M, plus 15% above $2M.
  - *Appeal or post-judgment collection:* an additional 5%.
  - A client may petition a court to approve a different contract (4-1.5(f)(4)(B)(ii)).
- **Medical liability.** The lawyer must provide Fla. Const. art. I, §26 in writing and orally explain it: the claimant keeps at least 70% of the first $250,000 and 90% of anything above that, unless the client waives this through a sworn waiver form with its own 3-business-day cancellation (4-1.5(f)(4)(B)(iii)).
- **Fee division with another firm:** at least 75% to the primary firm and at most 25% to the secondary firm unless a court approves otherwise (4-1.5(f)(4)(D)). Relevant when intake "refers out" a case and the firm keeps a referral fee.
- **Records:** the fee contract and closing statement are kept for 6 years after the closing statement is signed (4-1.5(f)(5)).
- **Mandatory fee arbitration clause:** needs a prior written recommendation to get independent advice and a bold-print NOTICE (4-1.5(i)).
- **Where it goes:** the client gets a signed copy, and the lawyer keeps it in the client file with the Statement of Client's Rights and, later, the closing statement.
- **Electronic signature:** M&M sends retainers "via email or text" for signature (first-party). Florida's Uniform Electronic Transaction Act says "If a provision of law requires a signature, an electronic signature satisfies such provision" (Fla. Stat. 668.50(7)). Whether this settles e-signing for Bar-rule purposes was **not confirmed** by a Florida Bar opinion (see Open Questions). **Medium**.

### 2.5 Florida "Statement of Client's Rights for Contingency Fees"

Source: same Chapter 4 PDF, Rule 4-1.5(f)(4)(C) and the Statement's text. **High**.

- **Required?** Yes, for PI, wrongful-death and tort property-damage contingency matters covered by 4-1.5(f)(4). "Before a lawyer enters into a contingent fee contract… the lawyer must provide the client with a copy of the statement of client's rights and must afford the client a full and complete opportunity to understand each of the rights as set forth in it."
- **Signed?** Yes. "A copy of the statement, signed by both the client and the lawyer, must be given to the client to retain and the lawyer must keep a copy in the client's file." It is kept with the fee contract and closing statement under the 6-year rule.
- **When?** Before the contract is signed. The required contract wording (4-1.5(f)(4)(A)(i)) has the client confirm receiving it beforehand.
- **What it says (11 numbered rights, summarised):**
  1. Fees can be negotiated, and the client may talk to other lawyers.
  2. The contract must be in writing and there is a 3-business-day cancellation right with no fee owed, though the client may owe actual costs. Withdrawal and discharge rules are explained.
  3. The right to know the lawyer's education, training and experience.
  4. Whether other lawyers will help and how fees will be shared; each firm must sign.
  5. Referral or association with other lawyers must be disclosed, with a new contract if that happens later.
  6. How costs and fees are paid, and whether the fee is calculated on the gross or net recovery.
  7. Possible adverse consequences of losing, including costs and the other side's fees.
  8. The right to approve a closing statement before any money is paid out.
  9. Progress updates.
  10. The client makes the final decision on settlement.
  11. Fee complaints may go to The Florida Bar (850/561-5600).
  It ends with client and attorney signature and date lines.
- **Statutory status:** "This statement is not a part of the actual contract between you and your lawyer" (the Statement's preamble).

### 2.6 HIPAA medical authorisation / records release, and letter of representation

- **HIPAA authorisation.** It is usually part of the sign-up package. A Maryland PI firm's sample sign-up letter encloses "the representation agreement and a medical authorization" and says it now usually sends retainers electronically (https://www.millerandzois.com/professional-attorney-information-center/forms-and-letters-for-personal-injury-lawyers/sample-correspondence/sample-letter-contingency-fee-agreement/). CASEpeer lists HIPAA authorisations among standard PI forms. **Medium**.
  - **Legally required elements (45 CFR 164.508(c)):**
    - a specific description of the information;
    - who may disclose it;
    - who may receive it;
    - the purpose of each use;
    - an expiration date or event;
    - the signature and date, plus a description of a personal representative's authority if one signs;
    - statements of the right to revoke in writing, whether treatment can be conditioned on signing, and that redisclosed information may no longer be protected;
    - plain language;
    - a copy to the individual.
  Source: https://www.law.cornell.edu/cfr/text/45/164.508 (eCFR redirected to a block page). **High**.
- **Letter of representation (LOR).** Sent after sign-up by the lawyer or case team, not by intake, to the at-fault insurer, the client's own insurer and others. It says the firm represents the client, directs all communication to the firm, and typically asks for policy limits and evidence preservation. M&M: "Your lawyer will contact the other side in your claim and inform them that Morgan & Morgan represents you." **Medium** (first-party, plus secondary descriptions such as https://www.shouselaw.com/ca/blog/attorney-letter-of-representation/). In Florida the policy-limits request can be made under Fla. Stat. 627.4137 (30-day sworn disclosure). **High** for the statute.
- **Crash reports (Florida).** For 60 days after filing, crash reports are available only to parties, their "legal representatives", insurers and some agencies, and the requester must file a sworn statement that the report will not be used for "commercial solicitation of accident victims" (Fla. Stat. 316.066(2)). **High**.
- **Letters of protection and medical referrals (Florida).** If the claimant was referred for treatment under a letter of protection, Fla. Stat. 768.0427(3) (from HB 837) requires disclosure of who referred them. A referral by the claimant's attorney is admissible, and the law-firm–provider financial relationship is relevant to bias. This matters if intake staff help callers "schedule doctor visits", a duty seen in some PI intake postings (Low for that practice). **High** for the statute.

### 2.7 Non-engagement / declination letter

- **Purpose:** to prove that the firm declined the case and that no attorney-client relationship exists. "Most of the malpractice claims in situations where a case hasn't been formally declined arise out of a missed statute of limitations or similar deadline." Florida courts judge the attorney-client relationship by the client's "subjective reasonable belief" (Bartholomew v. Bartholomew, 611 So. 2d 85 (Fla. 2d DCA 1992), cited in Opinion 24-1). **High** for the case citation as quoted in 24-1; **Medium** for the risk-management guidance.
- **Contents** (Minnesota Lawyers Mutual guide, https://mlmins.com/Library/Non-Engagement%20Guide.pdf; MLM is a malpractice insurer, not a Florida source):
  - "A clear and unambiguous statement that you are declining representation";
  - that declining "does not necessarily mean that the person does not have a claim or that other lawyers might not differ";
  - advice to "act quickly to seek other legal counsel";
  - that "statutes of limitation can bar the person's claim";
  - **do not** comment on the merits, and "Do not specifically state your calculations for the time limitations";
  - consider certified mail with return receipt;
  - keep copies (MLM says at least ten years);
  - enter the person in the conflict system.
  The sample letter (Form NE01) says the firm "is not expressing an opinion on whether you will prevail" and that "whatever claim, if any, that you have may be barred by the passage of time." **Medium**.
- **Florida add-on (practice, not required):** refer to The Florida Bar Lawyer Referral Service, 800-342-8011, Mon–Fri 8:00–5:30, a 30-minute consultation for no more than $25, with online referral available 24/7 (https://www.floridabar.org/public/lrs/). **High** for the facts about the service; **Low** that firms routinely include it.
- **Who signs and where it goes:** the firm or a lawyer signs. It is filed in a non-engagement file (MLM advises against opening a full client file) and in the conflict database.

### Implications for an AI intake specialist (Section 2)

- **Must produce:**
  - a lead or intake record with structured fields matching M&M's form and first-call questions, plus incident date, first-treatment date, insurers, police report, prior counsel and marketing source;
  - a conflict-check request with the minimum names needed, sent before the detailed narrative;
  - an attorney-review summary;
  - a disposition: qualified for attorney review, signed, pending signature, declined, referred out, existing-client routing, or not a prospect.
- **Must ensure** that for any Florida PI sign-up, the Statement of Client's Rights is delivered and signed *before* the contingency contract. The contract must carry the two required clauses and must also be signed by a lawyer.
- **Must not** explain or interpret the fee agreement or its terms beyond factual delivery (Opinion 88-6: "no legal advice concerning… the representation agreement"). Questions about it go to a lawyer.
- **Must trigger** a written non-engagement letter for every declined lead. It must not calculate or state the person's limitation deadline.

---

## Section 3 — Handoff to the attorney

- **Path at M&M:** intake staff consult and gather facts. An **Intake Attorney** reviews materials such as police reports and photographs and makes "real-time case acceptance decisions". It is the Intake Attorney who provides attorney-level reassurance before the retainer is signed and coordinates onboarding with managing partners and attorneys nationwide. Source: https://job-boards.greenhouse.io/morganmorganjobsapplynow/jobs/6150043004 — **Medium-High**.
- **Who decides to accept:** a lawyer. Opinion 88-6 says "the initial and continuing relationship with the client is the responsibility of the lawyer" and that the lawyer must "evaluate all information obtained by a nonlawyer employee… and… subsequently confer with the client and establish a personal and continuing relationship." Opinion 24-1: a lawyer "may not delegate to generative AI any act that could constitute the practice of law… or any other function that requires a lawyer's personal judgment and participation." **High**.
- **Timing at M&M:** "call you within 24 hours"; if the firm can help, "we will send documents to sign via email"; an attorney and team are "typically" assigned "within a week". **Medium-High**.
- **E-sign versus in-person sign-up:** M&M intake staff send and collect retainers by email or text. Other PI firms use field investigators who meet clients, including at home. This was seen only in search snippets, as the postings were expired or unreachable (**Low**). In-person contact must follow an inbound request: Rule 4-7.18(a) bans in-person or telephone solicitation of people with no prior relationship, and the comment says "An accident scene, a hospital room of an injured person, or a doctor's office" are not acceptable venues for initiating contact. **High** for the rule.
- **What intake can and cannot say** (Opinions 88-6 and 24-1; Rules 4-5.3, 4-5.5, 4-7.13). **High**:
  - **Can:** say it is a nonlawyer or AI; gather facts; explain process logistics (next steps, who will call, what documents to send); deliver the firm's standard documents.
  - **Cannot:**
    - give legal advice about the case or the fee agreement;
    - assess the merits or value of the claim;
    - predict or guarantee results (Rule 4-7.13(b)(1) bars statements a prospect "can reasonably interpret as a prediction or guaranty of success or specific results");
    - make comparative claims about the firm's skill that cannot be verified (4-7.13(b)(3));
    - promise financial help, since lawyers may advance only court costs and litigation expenses (Rule 4-1.8(e));
    - accept the case on the firm's behalf.
- **Declined leads:** written non-engagement letter, entry in the conflict system, optional referral (Section 2.7). Litify tracks "Turn-down rate" and "Referral rate", which shows that declination and referral-out are standard dispositions. **Medium**.
- **Still-unsigned leads:** the Intake Attorney and CSRs follow up (Section 1.7). The 3-business-day cancellation window starts at signing, so a "signed" case can still be cancelled in writing within that window (4-1.5(f)(4)(A)(ii)). **High**.

### Implications for an AI intake specialist (Section 3)

- **Must** hand off with a complete, reviewable package (Section 2.2), and must say in plain terms that an attorney decides whether the firm can take the case.
- **Must not** tell a caller "you have a case", "your case is worth X", or "we'll win". It must not answer "should I sign?" or "what does clause N mean?" Those are routed to a lawyer.
- **Must** handle the "signed but within 3 business days" status and the "declined, letter required" status as distinct states.
- **Must not** start in-person or phone solicitation. Outbound calls are limited to people who contacted the firm or asked for a callback (see Section 4.5).

---

## Section 4 — Florida rules that constrain intake

### 4.1 Statute of limitations (Fla. Stat. 95.11) and HB 837

- **The general negligence period is now 2 years.** Current Fla. Stat. 95.11(5) is headed "WITHIN TWO YEARS" and paragraph (a) reads "An action founded on negligence." (2026 Florida Statutes; history line includes s. 3, ch. 2023-15). Source: http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0000-0099/0095/Sections/0095.11.html — **High**.
- **HB 837 made the change.** The enrolled CS/CS/HB 837, Section 3, struck "(a) An action founded on negligence." from 95.11(3), "WITHIN FOUR YEARS", and added it to the "WITHIN TWO YEARS" subsection, which was numbered (4) at the time and has since been renumbered (5). Source: https://www.flsenate.gov/Session/Bill/2023/837/BillText/er/PDF — **High**.
- **Applicability and effective date.** "Section 28. The amendments made by this act to s. 95.11, Florida Statutes, apply to causes of action accruing after the effective date of this act." "Section 31. This act shall take effect upon becoming a law." The bill page gives chapter law 2023-15, effective **March 24, 2023** (https://www.flsenate.gov/Session/Bill/2023/837). **High**.
- **Accrual.** "A cause of action accrues when the last element constituting the cause of action occurs" (Fla. Stat. 95.031(1)). For a typical injury claim this is the date of the injury. **High** for the statute; **Medium** that this equals the incident date in a given case.
  - **Practical consequence (inference, Medium):** a negligence claim that accrued on or before March 24, 2023 keeps the 4-year period, so the last of those run out around March 24, 2027. As of 2026-10-07, some pre-reform claims are therefore still within time. Exactly how an incident *on* March 24, 2023 is treated was not checked.
- **Exceptions to flag at intake** (all **High** unless noted):
  - *Wrongful death:* 2 years (95.11(5)(e)).
  - *Medical malpractice:* 2 years from the incident or from when it was or should have been discovered, with a 4-year outer limit. The outer limit does not bar an action on behalf of a minor brought on or before the child's eighth birthday (95.11(5)(c)). Pre-suit notice and investigation requirements also apply (ch. 766; not researched in detail).
  - *Intentional torts* (assault, battery, etc.): still 4 years (95.11(3)(n)). Note that negligent-security claims are negligence claims.
  - *Claims against the state, agencies or subdivisions (sovereign immunity):* written notice to the agency, and, except for municipalities, counties and the Florida Space Authority, also to the Department of Financial Services, "within 3 years after such claim accrues" (768.28(6)(a)). Suit must be filed within 4 years (768.28(14)). Damages caps are $200,000 per person and $300,000 per incident (768.28(5)(a)). Source: http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0700-0799/0768/Sections/0768.28.html
  - *Minors:* minority tolls the period only while no parent, guardian or guardian ad litem exists, or while one has an adverse interest, subject to a 7-year cap. "A disability or other reason does not toll" except as listed (Fla. Stat. 95.051). So for most minors with a parent, the period is **not** tolled. **High** for the statute; **Medium** for the practical reading.
- **Other HB 837 changes that affect screening:** modified comparative negligence, where more than 50% at fault means no recovery (768.81(6)), and letter-of-protection disclosures (768.0427). **High**.

### 4.2 Rule 4-1.18 — duties to prospective clients

- **(a)** "A person who consults with a lawyer about the possibility of forming a client-lawyer relationship with respect to a matter is a prospective client."
- **(b)** Even if no relationship follows, the lawyer "may not use or reveal that information" except as Rule 4-1.9 allows for former clients.
- **(c)** The lawyer, and through imputation the firm, may be disqualified from representing someone materially adverse in the same or a substantially related matter if the lawyer received information "that could be used to the disadvantage of that person".
- **(d)** Representation is still allowed with informed consent of both sides confirmed in writing, *or* if the lawyer "took reasonable measures to avoid exposure to more disqualifying information than was reasonably necessary to determine whether to represent the prospective client", is timely screened and takes no part of the fee, and prompt written notice is given.
- **The comment explains when a consultation happens:** it is "likely to have occurred if a lawyer, either in person or through the lawyer's advertising in any medium, specifically requests or invites the submission of information about a potential representation without clear and reasonably understandable warnings and cautionary statements that limit the lawyer's obligations". Lawyers "should limit the initial consultation to only information as reasonably appears necessary". A lawyer may condition a consultation on the person's informed consent that nothing disclosed will prevent the firm from representing a different client.

Source: RRTFB Ch. 4 (Oct. 1, 2026) — **High**.

**What this means for when conflict checks happen:** collect the identifying names (caller, other parties, insured or owner) and run the conflict check *before* taking the full narrative and medical details. Under (d)(2), limiting what is collected early is what preserves the firm's ability to screen and keep representing an existing client.

### 4.3 Florida Bar Ethics Opinion 24-1 (generative AI)

- **It exists.** Florida Bar Ethics Opinion 24-1, dated January 19, 2024. "Advisory ethics opinions are not binding." Source: https://www.floridabar.org/etopinions/opinion-24-1/ — **High**.
- **Headnote:** lawyers may use generative AI but "must protect the confidentiality of client information, provide accurate and competent services, avoid improper billing practices, and comply with applicable restrictions on lawyer advertising… Generative AI chatbots that communicate with clients or third parties must comply with restrictions on lawyer advertising and must include a disclaimer indicating that the chatbot is an AI program and not a lawyer or employee of the law firm."
- **Intake specifically:**
  - "Lawyers who rely on generative AI for research, drafting, communication, and client intake risk many of the same perils as those who have relied on inexperienced or overconfident nonlawyer assistants."
  - It applies the Opinion 88-6 conditions to AI: identify nonlawyer status, limit questions to facts, and give no legal advice about the matter "or the representation agreement and refer any legal questions back to the lawyer."
  - "This guidance is especially useful as law firms increasingly utilize website chatbots for client intake… it presents additional risks, including that a prospective client relationship or even a lawyer-client relationship has been created without the lawyer's knowledge."
  - "a lawyer should be wary of utilizing an overly welcoming generative AI chatbot that may provide legal advice, fail to immediately identify itself as a chatbot, or fail to include clear and reasonably understandable disclaimers limiting the lawyer's obligations."
- **Disclosure and advertising:** "To avoid confusion or deception, a lawyer must inform prospective clients that they are communicating with an AI program and not with a lawyer or law firm employee." The opinion also says "a lawyer should consider including screening questions that limit the chatbot's communications if a person is already represented by another lawyer." The lawyer is "ultimately responsible in the event the chatbot provides misleading information… or communicates in a manner that is inappropriately intrusive or coercive." It links this to Rule 4-7.13(b)(5), which treats as misleading "a voice or image that creates the erroneous impression that the person speaking… is… a lawyer or employee of the advertising firm unless the advertisement contains a clear and conspicuous disclaimer". The opinion is written about website chatbots, but this rule expressly covers a *voice*.
- **Confidentiality:** research the provider's data retention, sharing and "self-learning" policies. It is "recommended that a lawyer obtain the affected client's informed consent prior to utilizing a third-party generative AI program if the utilization would involve the disclosure of any confidential information."
- **Supervision:** Rule 4-5.3 standards apply by analogy. The lawyer must have policies giving reasonable assurance that the AI's conduct fits professional obligations, and must review its work product.
- **Delegation limit:** a lawyer "may not delegate to generative AI any act that could constitute the practice of law such as the negotiation of claims or any other function that requires a lawyer's personal judgment and participation."
- **Later rule amendments:** the current Chapter 4 comments to Rules 4-1.1 (competence), 4-1.6 (confidentiality), 4-5.1 and 4-5.3 (supervision) now refer to generative AI explicitly. For example, the 4-5.3 comment says "A lawyer should also consider safeguards when assistants use technologies such as generative artificial intelligence", and it lists "using generative artificial intelligence" among nonlawyer services outside the firm. Secondary sources date these amendments to an August 29, 2024 Florida Supreme Court order, effective October 28, 2024 (https://ediscoverytoday.com/2024/09/03/florida-supreme-court-adopted-amendments-to-rules-for-generative-ai-artificial-intelligence-trends/). **High** for the current text; **Medium** for the adoption dates.

### 4.4 Florida call-recording consent (Fla. Stat. 934.03)

- It is lawful to intercept a wire, oral or electronic communication "when all of the parties to the communication have given prior consent to such interception" (934.03(2)(d)). Violation is generally "a felony of the third degree" (934.03(4)(a)). Source: http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0900-0999/0934/Sections/0934.03.html — **High**.
- A telephone call is a "wire communication" (934.02(1)), and that definition has no expectation-of-privacy element. "Oral communication" (934.02(2)) does require an expectation of privacy. **High**.
- By contrast, the federal Wiretap Act requires only one party's consent (18 U.S.C. 2511(2)(d)). **High**. For calls involving Florida callers, the Florida all-party rule is the binding one.
- **Implication:** a recorded intake call needs a clear recording notice and consent at the start of the call. Litify notes that attorneys receive "call recordings" with intake records, so recordings are common.

### 4.5 Solicitation and advertising rules as they bear on inbound and outbound intake

- **Rule 4-7.18(a)** bars a lawyer, or the lawyer's "employees or agents", from soliciting in person professional employment from a prospective client with no family or prior professional relationship when pecuniary gain is a significant motive. "Solicit" includes contact "in person, by telephone, by electronic means that include real-time communication face-to-face such as video telephone or video conference". The comment adds that "An accident scene, a hospital room of an injured person, or a doctor's office" do not count as permitted business settings. **High**.
- **Rule 4-7.18(b)** (written communications): no targeted written solicitation about PI or wrongful death "unless the accident or disaster occurred more than 30 days prior to the mailing". Permitted mailings must be marked "advertisement", and emails must begin with "Advertisement". These requirements "do not apply to… communications by the lawyer at a prospective client's request" (4-7.18(b)(3)). **High**.
- **Fla. Stat. 817.234(8)(b):** "A person may not solicit or cause to be solicited any business from a person involved in a motor vehicle accident by any means of communication other than advertising directed to the public for the purpose of making motor vehicle tort claims or claims for personal injury protection benefits… within 60 days after the occurrence of the motor vehicle accident." This is a third-degree felony. Under (8)(c), lawyers may not solicit accident victims by in-person or telephone contact at their residence after the 60 days either. **High**.
- **Implication:** outbound intake calls and texts are acceptable as **follow-up with people who contacted the firm** or asked for contact (the M&M web form collects explicit consent to calls and texts). Cold outreach to accident victims is prohibited and in some cases a crime. Any outbound script must avoid predictions of results (4-7.13(b)(1)) and unverifiable superiority claims (4-7.13(b)(3)).

### Implications for an AI intake specialist (Section 4)

- **Must:**
  - say at the start of every call that it is an AI and not a lawyer or firm employee;
  - obtain consent to record from all parties before recording;
  - ask early whether the caller already has a lawyer for this matter;
  - run a minimal-information conflict screen before the detailed narrative;
  - capture the exact incident date and identify the limitation regime (pre or post March 24, 2023 accrual, government defendant, medical malpractice, wrongful death, minor) so an attorney can calendar it.
- **Must not:**
  - give legal advice, including about the limitation deadline itself (escalate urgent-limitation leads instead);
  - evaluate the merits or value of the case;
  - interpret the fee contract;
  - claim superiority or predict outcomes;
  - make unsolicited outbound contact with accident victims.
- **Must produce** auditable records: the disclosure given, the recording consent, the conflict-screen result, and the disposition. These support the lawyer's Rule 4-5.3 supervision and the Rule 4-1.18 screening defence.

---

## Section 5 — Glossary

| Term | Meaning | Source / confidence |
|---|---|---|
| **PNC (potential new client)** | A prospective client lead in intake. Used in large PI firms' job titles, e.g. "PNC Intake Auditor & Sign-Up Coordinator". | Thomas J. Henry posting — Medium |
| **Prospective client** | The legal term (Rule 4-1.18(a)): a person who consults a lawyer about possibly forming a client-lawyer relationship. Triggers confidentiality and conflict duties. | RRTFB — High |
| **Lead / intake record** | The CRM record of a PNC: contact details, case type, facts, source, disposition. | Litify, Lawmatics — Medium |
| **Sign-up / signed case** | A PNC who has signed the firm's fee agreement (retainer) and become a client. "Sign-up coordinator" is a job title. | Thomas J. Henry; M&M — Medium |
| **Retainer (PI usage)** | In PI firms, "retainer" usually means the signed contingency-fee agreement, not an advance payment. M&M: "signed retainer agreements". Distinct from an hourly-billing retainer deposit. Rule 4-1.5(f)(2) covers a lawyer "who accepts a retainer or enters into an agreement… contingent… on the successful prosecution or settlement". | M&M postings; RRTFB — High/Medium |
| **Contingency (contingent) fee** | A fee paid only from a recovery, as a percentage. In Florida PI cases it is capped by the 4-1.5(f)(4)(B) schedule. M&M markets it as "The Fee Is Free® — only pay if we win". | RRTFB; forthepeople.com — High |
| **Statement of Client's Rights** | The mandatory Florida disclosure for contingency-fee PI matters, signed by client and lawyer before the contract. | RRTFB 4-1.5(f)(4)(C) — High |
| **3-day (3-business-day) cancellation** | The client's right to cancel a Florida PI contingency contract in writing within 3 business days without owing a fee. | RRTFB 4-1.5(f)(4)(A)(ii) — High |
| **Closing statement** | An itemised settlement statement of fees, costs and the client's net recovery, signed by the client and every participating lawyer. | RRTFB 4-1.5(f)(5) — High |
| **Declination / non-engagement / turn-down** | The firm declines the case, confirmed in a non-engagement letter. "Turn-down rate" is a KPI. | MLM guide; Litify — Medium |
| **Refer out / referral fee / co-counsel** | Sending a case to another firm. In Florida PI the secondary firm's share is capped at 25% unless a court approves more. | RRTFB 4-1.5(f)(4)(D); Litify "Referral rate" — High/Medium |
| **Conflict check** | A search of parties' names against current, former and prospective clients before accepting, or before taking detailed facts. | RRTFB 4-1.18; Clio — High/Medium |
| **Intake attorney** | A lawyer dedicated to reviewing and accepting intake leads in real time, without a litigation caseload. | M&M posting — Medium-High |
| **Case Consultant / Case Intake Specialist (CSR)** | M&M's titles for front-line intake staff in the Case Control Center. | M&M postings — Medium-High |
| **Case manager** | The post-sign-up staff member who manages treatment tracking, records, and client communication under the attorney. M&M assigns "an attorney and legal team" within about a week. | forthepeople.com — Medium |
| **Letter of representation (LOR)** | A notice to insurers and other parties that the firm represents the client; directs contact to the firm and usually requests policy limits. | Secondary; M&M process page — Medium |
| **Letter of protection (LOP)** | A medical provider treats in exchange for payment from any recovery. Florida 768.0427 requires disclosures, including attorney referrals. | Fla. Stat. 768.0427 — High |
| **PIP** | Florida no-fault personal injury protection: 80% of reasonable medical expenses up to $10,000 ($2,500 without an emergency medical condition), and only if treatment starts within 14 days. | Fla. Stat. 627.736 — High |
| **Policy limits disclosure** | Insurer's sworn statement of coverage, due within 30 days of a claimant's written request. | Fla. Stat. 627.4137 — High |
| **SOL (statute of limitations)** | The filing deadline. Florida general negligence is 2 years for claims accruing after March 24, 2023 and 4 years before that. | Fla. Stat. 95.11; ch. 2023-15 — High |
| **Want % / conversion %** | Intake KPIs: share of leads the firm wants, and share converted to signed cases. | Litify — Medium |
| **Speed to lead** | Time from inquiry to first live contact. M&M promises a call within 24 hours after a web form. | forthepeople.com — Medium |
| **Tracking number** | A unique phone number per ad, campaign or page, used to attribute calls to a marketing source. | CallRail, Lawmatics — Medium |

---

## Verification results — the five claims

| # | Claim | Result | Details and citation |
|---|---|---|---|
| 1 | Florida requires a Statement of Client's Rights for contingency-fee cases, plus fee caps, plus a 3-day cancellation right. | **Confirmed, with refinements** | All three are in Rule 4-1.5(f)(4). (a) The Statement is required for **PI, wrongful-death and tort property-damage** contingency matters (the (f)(4) scope), not for every contingency matter. It must be given *before* the contract and **signed by both client and lawyer**, and the client keeps a copy. (b) The "caps" are a schedule above which fees are *presumed* clearly excessive without court approval (33⅓%/40% up to $1M, 30% of $1M–2M, 20% above $2M, and so on). (c) The cancellation right is **3 business days**, must be in writing, and no fee is owed, though the lawyer may be reimbursed amounts reasonably advanced. Source: https://www-media.floridabar.org/uploads/2026/10/2027_04-OCT-Chapter-4-RRTFB.pdf |
| 2 | Florida Bar Ethics Opinion 24-1 addresses AI chatbots used for intake. | **Confirmed** | Opinion 24-1 (Jan. 19, 2024; advisory, not binding) explicitly discusses "website chatbots for client intake". It applies Opinion 88-6's nonlawyer-interview limits, warns against "overly welcoming" chatbots, requires telling prospects they are "communicating with an AI program and not with a lawyer or law firm employee", and recommends screening questions for already-represented persons. https://www.floridabar.org/etopinions/opinion-24-1/ |
| 3 | Litify originated within Morgan & Morgan, and Morgan & Morgan uses it. | **Confirmed (Medium), with a nuance** | LawNext (legal-tech trade press): Litify "was developed by a team of people who came out of Morgan & Morgan" and launched in 2016. Wikipedia: co-founded in 2016 by John Morgan and Reuven Moskowitz, "originally developed for internal use". Use: Litify's own case study quotes M&M's Matt Morgan and says M&M "started using Litify for case management in 2019", and M&M's Intake Attorney posting prefers "Salesforce or Litify" experience. Litify's own About page gives only "founded in 2016" and does not mention M&M. The Bessemer press release (HTTP 403) could not be read. Sources: https://lawnext.com/2022/06/on-lawnext-podcast-litify-coo-ari-treuhaft-on-why-the-practice-management-company-considers-itself-a-unique-category-of-legal-tech.html ; https://en.wikipedia.org/wiki/Morgan_%26_Morgan ; https://www.litify.com/liticast/standardizing-attorney-performance-morgan-and-morgan/ ; https://www.litify.com/about |
| 4 | HB 837 (2023) cut Florida's general negligence SOL from 4 to 2 years for causes of action accruing after its effective date. | **Confirmed** | Enrolled HB 837, §3, moves "An action founded on negligence" from 95.11(3) ("WITHIN FOUR YEARS") to the two-year subsection. §28: the 95.11 amendments "apply to causes of action accruing after the effective date of this act". §31: effective "upon becoming a law", which was March 24, 2023 (ch. 2023-15). It is now codified at 95.11(5)(a). https://www.flsenate.gov/Session/Bill/2023/837/BillText/er/PDF ; https://www.flsenate.gov/Session/Bill/2023/837 |
| 5 | Florida is an all-party-consent state for recording calls. | **Confirmed** | Fla. Stat. 934.03(2)(d) makes interception lawful only "when all of the parties to the communication have given prior consent", and violation is a third-degree felony (934.03(4)(a)). Telephone calls are "wire communications" with no expectation-of-privacy element (934.02(1)). http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0900-0999/0934/Sections/0934.03.html |

---

## Open questions (not settled by the sources)

1. **After-hours handling at M&M.** The website says "Contact us 24/7", but Case Control Center postings give staffed hours of roughly 7–8 AM to 9 PM. Who answers overnight (an outsourced vendor, voicemail, an AI, or another time zone's staff) is undocumented.
2. **M&M's internal intake script, qualification checklist and memo format.** These are not public. The web form fields and the "what/where/when/who" questions are the only first-party evidence.
3. **Who signs the contingency contract for the firm, and when.** Rule 4-1.5(f)(2) requires a lawyer's signature. Whether M&M's e-sent retainers are pre-signed by a lawyer, countersigned after the client signs, or signed by the Intake Attorney is unknown.
4. **E-delivery of the Statement of Client's Rights.** No Florida Bar opinion was found that addresses delivering and signing the Statement electronically, or what satisfies "a full and complete opportunity to understand each of the rights" when signing remotely. Fla. Stat. 668.50(7) generally validates e-signatures, but its application to Bar-rule signature requirements was not confirmed.
5. **When follow-up on unsigned leads stops.** No authoritative cadence or cutoff was found. Vendor content describes "multi-touch sequences" without stop rules. It is also unsettled whether a lead that goes cold should automatically get a non-engagement letter.
6. **Field sign-ups at M&M.** Whether M&M uses in-person sign-up staff, and under what policies, was not documented. Other PI firms' "investigator" roles with home visits were seen only in search snippets.
7. **The exact cutoff for HB 837.** Whether a cause of action that accrued *on* March 24, 2023 is "after the effective date" was not researched (no case law reviewed).
8. **Opinion 24-1 and voice agents.** The opinion addresses website chatbots. Its application to a *voice* AI agent is an inference, strongly supported by Rule 4-7.13(b)(5)'s explicit reference to "a voice".
9. **Informed consent to use third-party AI with a prospective client's information.** Opinion 24-1 "recommends" informed consent before disclosing confidential information to third-party AI. How this applies to a *prospective* client at first contact, before any relationship exists, is not addressed.
10. **Clio 2024 secret-shopper figures.** These were taken from a secondary report; Clio's own press page returned HTTP 403. The ABA Law Practice Magazine intake article also returned HTTP 403 and was not read.
11. **Medical malpractice pre-suit requirements (ch. 766)** and **wrongful-death claimant rules (768.16–.26)** were only noted, not researched.
12. **The "VIP Client Intake Specialist" role at M&M** (attorney-generated and external-firm referrals) was seen only in a search snippet. The posting was no longer available.

---

## Sources

### Primary — Florida statutes, legislation, rules, ethics opinions, federal law
- Rules Regulating The Florida Bar, Chapter 4 (Rules of Professional Conduct), RRTFB October 1, 2026 — https://www-media.floridabar.org/uploads/2026/10/2027_04-OCT-Chapter-4-RRTFB.pdf (index: https://www.floridabar.org/rules/rrtfb/). Read in full text for Rules 4-1.1 cmt, 4-1.5(f)–(i) and the Statement of Client's Rights, 4-1.6 cmt, 4-1.8(e), 4-1.18, 4-4.2 cmt, 4-5.1 cmt, 4-5.3, 4-7.13, 4-7.18.
- Florida Bar Ethics Opinion 24-1 (Jan. 19, 2024) — https://www.floridabar.org/etopinions/opinion-24-1/
- Florida Bar Ethics Opinion 88-6 (Apr. 15, 1988) — https://www-media.floridabar.org/uploads/2017/04/FL-Bar-Ethics-Op-88-6-1.pdf (HTML page https://www.floridabar.org/etopinions/etopinion-88-6/ did not render the text)
- CS/CS/HB 837 (2023), bill page — https://www.flsenate.gov/Session/Bill/2023/837 ; enrolled text — https://www.flsenate.gov/Session/Bill/2023/837/BillText/er/PDF
- Fla. Stat. 95.11 — http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0000-0099/0095/Sections/0095.11.html (also https://www.flsenate.gov/Laws/Statutes/2024/95.11)
- Fla. Stat. 95.031 — http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0000-0099/0095/Sections/0095.031.html
- Fla. Stat. 95.051 — http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0000-0099/0095/Sections/0095.051.html
- Fla. Stat. 768.28 — http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0700-0799/0768/Sections/0768.28.html
- Fla. Stat. 768.0427 — http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0700-0799/0768/Sections/0768.0427.html
- Fla. Stat. 934.02 — http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0900-0999/0934/Sections/0934.02.html
- Fla. Stat. 934.03 — http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0900-0999/0934/Sections/0934.03.html
- Fla. Stat. 627.736 — http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0600-0699/0627/Sections/0627.736.html
- Fla. Stat. 627.4137 — http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0600-0699/0627/Sections/0627.4137.html
- Fla. Stat. 817.234 — http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0800-0899/0817/Sections/0817.234.html
- Fla. Stat. 316.066 — http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0300-0399/0316/Sections/0316.066.html
- Fla. Stat. 668.50 — http://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0600-0699/0668/Sections/0668.50.html
- 45 CFR 164.508 (via Cornell LII; eCFR redirected to a block page) — https://www.law.cornell.edu/cfr/text/45/164.508
- 18 U.S.C. 2511 (via Cornell LII) — https://www.law.cornell.edu/uscode/text/18/2511
- The Florida Bar Lawyer Referral Service — https://www.floridabar.org/public/lrs/

### First-party — Morgan & Morgan
- Homepage and free case evaluation form — https://www.forthepeople.com/
- "What Is Morgan & Morgan's Process Like?" (2/6/2025) — https://www.forthepeople.com/blog/what-morgan-morgans-process/
- FAQ — https://www.forthepeople.com/faq/
- Careers board (Greenhouse) — https://job-boards.greenhouse.io/morganmorganjobsapplynow
  - Case Consultant (Longwood, FL) — https://job-boards.greenhouse.io/morganmorganjobsapplynow/jobs/6146478004
  - Case Intake Specialist – CSR (Las Vegas, NV) — https://job-boards.greenhouse.io/morganmorganjobsapplynow/jobs/6147389004
  - Intake Attorney (Longwood, FL) — https://job-boards.greenhouse.io/morganmorganjobsapplynow/jobs/6150043004
  - Nurse Intake Specialist — https://job-boards.greenhouse.io/morganmorganjobsapplynow/jobs/6218169004
  - Older posting URLs that now redirect to the board (not usable): .../jobs/5457916004, .../5579649004, .../5970256004, .../5840518004

### First-party — vendors and other firms
- Litify, intake management — https://litify.com/platform-2021/intake-management
- Litify, "How leading plaintiff firms use Litify to optimize marketing and intakes" — https://www.litify.com/blog/how-leading-plaintiff-firms-use-litify-to-optimize-marketing-and-intakes
- Litify, Morgan & Morgan case study — https://www.litify.com/liticast/standardizing-attorney-performance-morgan-and-morgan/ (also https://www.litify.com/resources/standardizing-attorney-performance-morgan-and-morgan)
- Litify, About — https://www.litify.com/about
- Lawmatics, personal injury — https://www.lawmatics.com/practice-areas/personal-injury-law/
- Clio blog (intake process; HTTP 403 on direct fetch, content taken from search summary) — https://www.clio.com/blog/fall-in-love-law-firm-client-intake-process/
- Clio press release on Legal Trends secret shopper (HTTP 403, not read) — https://www.clio.com/about/press/clios-legal-trends-report-reveals-law-firms-struggle-to-respond-to-client-inquiries/
- CASEpeer, PI client intake form — https://www.casepeer.com/blog/personal-injury-client-intake-form
- CASEpeer, PI forms — https://www.casepeer.com/blog/personal-injury-forms/
- Alert Communications — https://www.alertcommunications.com/
- CallRail, "Call Tracking 101 for Law Firms" (seen in search, not opened) — https://cdn.mediavalet.com/usva/callrail/36h_F7RHw0iJWPNWFIn9VQ/RdTHaxHkVU6EJLoR5fWXew/Original/Call%20Tracking%20101%20for%20Law%20Firms-CallRail%20%281%29.pdf
- Thomas J. Henry Law, PNC Intake Auditor & Sign-Up Coordinator — https://www.jobtarget.com/jobs/jt-cxjbxb46u3/pnc-intake-auditor-and-sign-up-coordinator-austin-texas
- Garza Law Firm, Intake/Reception Specialist — https://recruiting.paylocity.com/Recruiting/Jobs/Details/4368879
- Employbridge, Intake Attorney (expired posting) — https://www.legal.io/jobs/5849718/Full-time/Intake-Attorney/Phoenix/Arizona
- Miller & Zois, sample retainer and medical authorisation letter — https://www.millerandzois.com/professional-attorney-information-center/forms-and-letters-for-personal-injury-lawyers/sample-correspondence/sample-letter-contingency-fee-agreement/
- Minnesota Lawyers Mutual, "Guidebook to Practice Forms and Letters: Non-Engagement" — https://mlmins.com/Library/Non-Engagement%20Guide.pdf

### Secondary (labelled as such where used)
- Wikipedia, Morgan & Morgan — https://en.wikipedia.org/wiki/Morgan_%26_Morgan
- LawNext, Litify COO Ari Treuhaft podcast — https://lawnext.com/2022/06/on-lawnext-podcast-litify-coo-ari-treuhaft-on-why-the-practice-management-company-considers-itself-a-unique-category-of-legal-tech.html
- Illinois Supreme Court Commission on Professionalism (2Civility), 2024 Clio Legal Trends Report — https://www.2civility.org/2024-clio-legal-trends-report-fixing-the-first-impression-problem-for-law-firms/
- eDiscovery Today, Florida Supreme Court AI rule amendments — https://ediscoverytoday.com/2024/09/03/florida-supreme-court-adopted-amendments-to-rules-for-generative-ai-artificial-intelligence-trends/
- Lawyerist, Smith.ai — https://lawyerist.com/news/choosing-between-ai-and-a-live-receptionist-smith-ai/
- Shouse Law, attorney letter of representation — https://www.shouselaw.com/ca/blog/attorney-letter-of-representation/
- Hinshaw & Culbertson, alert on Opinion 24-1 (seen in search only) — https://www.hinshawlaw.com/en/insights/lawyers-for-the-profession-alert/florida-bar-advisory-opinion-24-1-gives-green-light-to-generative-ai-use-by-lawyers-with-four-ethical-caveats

### Attempted but not accessible
- ABA Law Practice Magazine, "Law's New First Impression: Transforming Client Intake" (HTTP 403) — https://americanbar.org/groups/law_practice/resources/law-practice-magazine/2025/march-april-2025/laws-new-first-impression-transforming-client-intake
- Bessemer / Litify press release (HTTP 403) — https://www.businesswire.com/news/home/20230209005162/en/Bessemer-Venture-Partners-Acquires-Majority-Stake-in-Litify-as-Legal-Tech-Company-Achieves-Profitability
- Several non-M&M PI intake job postings (expired, 404, or redirected), including Paylocity 2410061 and 4166254, CareerPlug 3221066, Crisp Recruit 5025168007, and Laborde Earles investigator.
