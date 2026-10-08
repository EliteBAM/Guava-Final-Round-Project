"""
Guava Legal Intake Specialist Agent taylored for Morgan and Morgan injury law firm on-spec.
Engineer: Robert Gehr 10-07-2026
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from pathlib import Path

import guava
from guava import logging_utils
from guava.events import AgentSpeechEvent, BotSessionEnded
from guava.helpers.rag import DocumentQA

import compliance
import conflicts
import crm
import esign
import intake
import qualification
import settings
import signing_server
import timezones

logger = logging.getLogger("guava.intro_agent")

CURRENT_DIR = Path(__file__).resolve().parent
RECORDS_DIR = CURRENT_DIR / "intake_records"

# begin by loading RAG documents from project directory and save it in a DocumentQA Guava Object.
# explicit utf-8: Windows defaults to cp1252 and fails to decode the docs
try:
    with open(CURRENT_DIR / "guava-docs.md", "r", encoding="utf-8") as f:
        document_qa = DocumentQA(documents=f.read(), namespace="guava-cli-intro")

except Exception as exc:
    document_qa = None
    logger.warning("Could not load Guava docs for RAG: %s", exc)

# after rag passed or failed, create an agent instance
agent = guava.Agent(
    name="Melody",
    organization="Morgan and Morgan",
    purpose=(
        "You are Morgan and Morgan's AI intake assistant for people who may have a personal injury case. "
        "You gather facts only: you never give legal advice, and never give opinions on fault, case strength, or case value. "
        "If anyone asks whether you are a real person, honestly confirm that you are an AI. "
        "Callers are often hurt or shaken, so be warm, calm and patient, but never salesy. "
        + compliance.RECORDING_POLICY
    ),
)

# per-call state, keyed by call.id. Never module globals per call: concurrent calls would share them.
CALL_STATE: dict[str, dict] = {}

# network I/O runs here, never inside a handler: Guava dispatches each call's events one at a time,
# so a slow API call in a handler would also delay escalation and every other event on that call
POOL = ThreadPoolExecutor(max_workers=8)

# tasks during which the agent's speech is captured for the disclosure check
DISCLOSURE_TASKS = ("disclosures", "consent_reconsider")


def call_state(call: guava.Call) -> dict:
    return CALL_STATE.setdefault(call.id, {
        "task": None,
        "disclosure_speech": [],
        "disclosure_retries": 0,
        "flags": set(),
        "disposition": None,
        "conflict_names": [],
        "conflict_attempts": 0,
        "conflict_status": None,
        "next_steps_speech": [],
    })


# setting up the agent - defining callback functions for the agent
@agent.on_call_start
def on_call_start(call: guava.Call):
    # no network I/O in here: the call isn't answered until this handler returns
    state = call_state(call)

    # recognize time of day for politeness and warmness in greeting. Feels less like a robot.
    # non-phone calls (webrtc, local) fall back to the firm's timezone
    from_number = call.call_info.from_number if call.call_info.call_type == "pstn" else None
    caller_time_of_day = timezones.get_time_of_day_str(timezones.get_timezone_for_number(from_number))
    greeting = f"Good {caller_time_of_day}. " if caller_time_of_day else ""

    # on call start, set some initial tasks and record log for session start
    logger.info("Call started (session: %s)", call.id)
    state["task"] = "introduction"

    call.set_task(
        "introduction",
        objective=(
            "Introduce yourself, your role, and collect the caller's name."
        ),
        checklist=[
            # carries the one immediate AI disclosure (Op. 24-1); the rest happen in the disclosures task
            guava.Say(
                f"{greeting}"
                "Thank you for calling Morgan and Morgan personal injury attorneys. "
                "My name is Melody, and I'm your legal intake specialist, powered by modern artificial intelligence. "
                "I'm here to listen and understand what you are going through and take you through the first steps toward legal representation."
            ),
            guava.Field(
                key="caller_name",
                field_type="text",
                description="Transition with 'May I,' then ask the caller for their name so you can address them personally.",
                required=True,
            ),
        ],
    )


# on question callback executes when agent determines it can't give a good answer contextually. Either an a place for autmated fallback, or RAG activation.
@agent.on_question
def on_question(call: guava.Call, question: str) -> str:
    logger.info("Question received: %s", question)

    # recording questions get the one approved, truthful answer from code, never RAG or the model's guess
    if compliance.is_recording_question(question):
        return compliance.RECORDING_ANSWER

    # fee and "should I sign?" questions are for an attorney (Op. 88-6): intake never interprets the agreement
    if compliance.is_fee_question(question):
        call_state(call)["flags"].add("fee_questions")
        return compliance.FEE_ANSWER

    if document_qa is not None:
        answer = document_qa.ask(question)
    else:
        answer = (
            "Unfortunately, I'm not able to answer that question right now, "
            "because my knowledge base didn't load. To fix that, I recommend "
            "verifying your network connection, then relaunching me."
        )
    logger.info("Answering...")
    return answer


@agent.on_task_complete("introduction")
def on_intro_complete(call: guava.Call):
    caller_name = call.get_field("caller_name")
    if caller_name:
        logger.info("Intro task complete. Caller name: %s", caller_name)
    start_disclosures(call)


def start_disclosures(call: guava.Call):
    state = call_state(call)
    state["task"] = "disclosures"
    state["disclosure_speech"].clear()
    call.set_task(
        "disclosures",
        objective="Deliver the required disclosures exactly, then get the caller's consent to record the call.",
        checklist=[
            # bridge as a plain string (Todo) so the model phrases it warmly in context
            "Thank the caller by name, and politely let them know that before you begin there are a few "
            "disclosures you're required to share with them.",
            guava.Say(compliance.DISCLOSURE_SCRIPT),
            guava.Field(
                key="recording_consent",
                field_type="multiple_choice",
                choices=["yes", "no"],
                question="Is it alright with you that this call is recorded?",
                description=compliance.CONSENT_FIELD_GUIDANCE,
                required=True,
            ),
        ],
    )


# capture what the agent actually said during the disclosures, so code (not the model) decides if they were delivered
@agent.on_agent_speech
def on_agent_speech(call: guava.Call, event: AgentSpeechEvent):
    state = call_state(call)
    if state["task"] in DISCLOSURE_TASKS:
        state["disclosure_speech"].append(event.utterance)
    elif state["task"] in CLOSING_TASKS:
        state["next_steps_speech"].append(event.utterance)


# runs when the disclosures task reports complete; returning (False, reason) makes the SDK retry the task
@agent.on_validate("recording_consent")
def validate_disclosures_spoken(call: guava.Call, value) -> bool | tuple[bool, str]:
    state = call_state(call)
    missing = compliance.missing_disclosure_phrases(" ".join(state["disclosure_speech"]))
    if not missing:
        return True

    if state["disclosure_retries"] < 1:
        state["disclosure_retries"] += 1
        logger.info("Disclosures incomplete (missing %s), retrying task (session: %s)", missing, call.id)
        return (
            False,
            "The required disclosures were not read in full. Read the disclosure statement exactly as written, "
            "then ask for consent to record again.",
        )

    # retry cap hit: don't loop the caller, flag the call for human review instead
    state["flags"].add("disclosure_unverified")
    logger.warning("Disclosures still unverified after retry, missing %s (session: %s)", missing, call.id)
    return True


@agent.on_task_complete("disclosures")
def on_disclosures_complete(call: guava.Call):
    if call.get_field("recording_consent") == "yes":
        on_consent_given(call)
        return

    # first decline: give the truthful reason, warn that a second decline ends the call, and confirm
    state = call_state(call)
    state["task"] = "consent_reconsider"
    call.set_task(
        "consent_reconsider",
        objective="The caller declined recording. Confirm whether they are sure, without pressuring them.",
        checklist=[
            guava.Say(compliance.CONSENT_RECONSIDER_SCRIPT),
            guava.Field(
                key="recording_consent_final",
                field_type="multiple_choice",
                choices=["agree_to_recording", "end_call"],
                # the "are you sure?" question is the end of the Say above, so it is always spoken verbatim
                description=(
                    "Their answer to whether they are sure they'd prefer not to be recorded. "
                    "If they now agree to the call being recorded, choose agree_to_recording. "
                    "If they confirm they do not want to be recorded, choose end_call. "
                    + compliance.CONSENT_FIELD_GUIDANCE
                ),
                required=True,
            ),
        ],
    )


@agent.on_task_complete("consent_reconsider")
def on_consent_reconsider_complete(call: guava.Call):
    if call.get_field("recording_consent_final") == "agree_to_recording":
        on_consent_given(call)
        return

    state = call_state(call)
    state["disposition"] = "consent_declined"
    call.hangup(final_instructions=compliance.CONSENT_DECLINED_INSTRUCTIONS)


def on_consent_given(call: guava.Call):
    state = call_state(call)
    state["flags"].add("recording_consent")
    state["disposition"] = "opening_complete"
    start_triage(call)


# Triage: is this a new prospective client calling about their own injury? Everyone else is routed away.
# Graph (MVP Flow Design.md, Part 3): Triage -> ConflictScreen | RouteMessage | Referral | Wrap
# Only the main path continues; every other route is a placeholder hangup (routing to teams is out of MVP scope).

# caller_type -> (who would handle the caller, disposition, must the confidentiality line be said)
TRIAGE_ROUTES = {
    "existing_client": ("their case team", "routed_existing_client", False),
    # Rule 4-1.6: adjusters and other parties' lawyers always hear that we can't confirm or discuss any client
    "insurance_or_attorney": ("the right team", "routed_insurance_or_attorney", True),
    "medical_provider": ("the client's case team", "routed_medical_provider", False),
    "other_legal_matter": ("the right department", "referred", False),
}


def start_triage(call: guava.Call):
    call_state(call)["task"] = "triage"
    call.set_task(
        "triage",
        objective="Find out why the caller is calling so you can direct them. Do not collect details about any incident yet.",
        checklist=[
            ("In your own words tell the caller that before you can begin collecting information on their incident, you want to confirm that "
            "they are calling on behalf of themselves to seek representation for a personal injury. If that is not the case, tell them that this line "
            "is for new client intake, but that if they tell you who they are and their reason for calling you may be able to redirect them."),
            guava.Field(
                key="caller_type",
                field_type="multiple_choice",
                choices=[
                    "new_injury_matter",
                    "existing_client",
                    "insurance_or_attorney",
                    "medical_provider",
                    "other_legal_matter",
                    "other",
                ],
                description=(
                    "Why they are calling. new_injury_matter: they or someone they know was hurt and they want help. "
                    "existing_client: they are already a Morgan and Morgan client calling about their case. "
                    "insurance_or_attorney: an insurance adjuster or a lawyer for another party. "
                    "medical_provider: a doctor's office, hospital, or lienholder calling about a patient. "
                    "other_legal_matter: a legal issue that isn't an injury, like divorce, criminal, or employment. "
                    "other: anything else, such as sales calls or wrong numbers. "
                    "If they start telling the whole story, gently let them know you'll get to the details in just a moment."
                ),
                required=True,
            ),
            guava.Field(
                key="on_behalf_of",
                field_type="multiple_choice",
                choices=["self", "someone_else", "not_applicable"],
                description=(
                    "Whether the person who was injured is the caller themselves. "
                    "If the call isn't about an injury, choose not_applicable without asking."
                ),
                required=True,
            ),
        ],
    )


@agent.on_task_complete("triage")
def on_triage_complete(call: guava.Call):
    state = call_state(call)
    caller_type = call.get_field("caller_type")
    on_behalf_of = call.get_field("on_behalf_of")
    logger.info("Triage complete: caller_type=%s on_behalf_of=%s (session: %s)", caller_type, on_behalf_of, call.id)

    # main route: a new prospective client, calling about their own injury
    if caller_type == "new_injury_matter" and on_behalf_of == "self":
        state["disposition"] = "triage_passed"
        start_conflict_screen(call)
        return

    # placeholder routes below: record who called, tell them who will reach out, and end the call

    # the injured person (or their estate's representative) must be the client, so the intake team arranges that contact
    if caller_type == "new_injury_matter":
        route_away(call, "our intake team", "routed_third_party")
        return

    if caller_type in TRIAGE_ROUTES:
        route_away(call, *TRIAGE_ROUTES[caller_type])
        return

    state["disposition"] = "not_a_prospect"
    call.hangup(final_instructions="Politely let them know this line is for people who've been injured, and wish them well.")


def route_away(call: guava.Call, team: str, disposition: str, confidential: bool = False):
    call_state(call)["disposition"] = disposition
    confidentiality = f"Say exactly: \"{compliance.CONFIDENTIALITY_SCRIPT}\" " if confidential else ""
    call.hangup(final_instructions=(
        f"{confidentiality}Let them know you'll have {team} reach out to them, then thank them and say goodbye. "
        "Don't ask any more questions or discuss any case."
    ))


# Conflict screen: collect only what the conflict check needs, before hearing the story (Rule 4-1.18).
# Graph (MVP Flow Design.md, Part 3): ConflictScreen -> Story | DeclineConflict | AttorneyEscalation | retry offer

def start_conflict_screen(call: guava.Call):
    call_state(call)["task"] = "conflict_min"
    call.set_task(
        "conflict_min",
        objective=(
            "Collect the few details needed for a conflict-of-interest check. "
            "Do not ask how the incident happened or about injuries yet."
        ),
        checklist=[
            "Thank them warmly. Explain that before they share the details of what happened, you need a few quick "
            "things so you can make sure the firm is free to help them.",
            guava.Field(
                key="caller_full_name",
                field_type="text",
                description="Their full legal name. Ask them to spell their last name.",
                required=True,
            ),
            guava.Field(
                key="adverse_parties",
                field_type="text",
                description=(
                    "The name of the other driver, business, or employer involved, if they know it. "
                    "It's fine if they don't know."
                ),
                required=False,
            ),
            guava.Field(key="incident_date", field_type="date", description="The date of the incident.", required=True),
            guava.Field(
                key="represented",
                field_type="multiple_choice",
                choices=["yes", "no", "not_sure"],
                question="Have you already hired a lawyer for this?",
                required=True,
            ),
        ],
    )


@agent.on_validate("incident_date")
def validate_incident_date(call: guava.Call, value) -> bool | tuple[bool, str]:
    try:
        incident = date(value["year"], value["month"], value["day"])
    except (TypeError, KeyError, ValueError):
        return (False, "The incident date wasn't a valid date. Ask the caller for it again.")
    if incident > date.today():
        return (False, "The incident date is in the future. Gently confirm the date with the caller.")
    return True


@agent.on_task_complete("conflict_min")
def on_conflict_min_complete(call: guava.Call):
    state = call_state(call)
    if call.get_field("represented") == "yes":
        state["flags"].add("represented")
        state["disposition"] = "routed_represented"
        call.hangup(final_instructions=compliance.REPRESENTED_INSTRUCTIONS)
        return

    names = [call.get_field("caller_full_name")]
    adverse = (call.get_field("adverse_parties") or "").strip()
    if adverse:
        names.append(adverse)
    else:
        state["flags"].add("adverse_unknown")
    state["conflict_names"] = names
    POOL.submit(run_conflict_check, call)


def run_conflict_check(call: guava.Call):
    """Worker: runs the conflict check off the handler thread, then sets the next task from the result."""
    state = call_state(call)
    state["conflict_attempts"] += 1
    status = conflicts.check_conflicts(state["conflict_names"])
    state["conflict_status"] = status
    logger.info("Conflict check attempt %d: %s (session: %s)", state["conflict_attempts"], status, call.id)

    if status == "clear":
        state["disposition"] = "conflict_clear"
        start_story(call)
    elif status == "conflict":
        start_conflict_decline(call)
    elif state["conflict_attempts"] < 2:
        state["task"] = "conflict_retry_offer"
        # set now, not on task completion: the outcome is a failed check unless a retry succeeds, and the model
        # sometimes ends the call itself on a "no thanks" before the task reports complete
        state["disposition"] = "conflict_check_failed"
        call.set_task(
            "conflict_retry_offer",
            objective="The conflict check couldn't be reached. Let the caller decide whether to try it once more.",
            checklist=[
                guava.Say(compliance.CONFLICT_ERROR_SCRIPT),
                guava.Field(
                    key="retry_choice",
                    field_type="multiple_choice",
                    choices=["retry", "no_retry"],
                    description=(
                        "Whether they'd like you to try the lookup again. If they say no, record that right away; "
                        "don't try to change their mind."
                    ),
                    required=True,
                ),
            ],
        )
    else:
        state["disposition"] = "conflict_check_failed"
        call.hangup(final_instructions=compliance.CONFLICT_FAILED_INSTRUCTIONS)


def start_conflict_decline(call: guava.Call):
    """Used by both the first check and the post-story re-check."""
    state = call_state(call)
    state["task"] = "conflict_decline"
    state["disposition"] = "declined_conflict"
    call.set_task(
        "conflict_decline",
        objective="Kindly let the caller know the firm can't take their matter, and help them find other help.",
        checklist=[
            "Gently prepare them: let them know you have an update on whether the firm is able to help.",
            guava.Say(compliance.CONFLICT_DECLINE_SCRIPT),
            "Answer any questions kindly. If they ask who or what the connection is, say you're not able to "
            "share any details about it.",
        ],
    )


@agent.on_task_complete("conflict_retry_offer")
def on_conflict_retry_offer_complete(call: guava.Call):
    if call.get_field("retry_choice") == "retry":
        POOL.submit(run_conflict_check, call)
        return
    call_state(call)["disposition"] = "conflict_check_failed"
    call.hangup(final_instructions=compliance.CONFLICT_FAILED_INSTRUCTIONS)


@agent.on_task_complete("conflict_decline")
def on_conflict_decline_complete(call: guava.Call):
    call.hangup(final_instructions="Thank them, wish them well in their recovery, and say goodbye.")


# Story: the caller's account in their own words, then only the details still missing. The fields come from the
# intake schema (intake.py): the common core here, then the case-type module in its own task.
# Graph: Story -> module -> Details* -> qualify -> DeclineConflict | NextSteps

# how each tier is asked (Story Stage Schema and Plan.md, 1.1)
TIER_GUIDANCE = {
    intake.CRITICAL: "Don't press if they don't know.",
    intake.IMPORTANT: "Ask once if they haven't already mentioned it.",
}


def unknown_hint(spec: intake.FieldSpec) -> str:
    """Every field needs a value for "I don't know": a field the model asked about but can't fill keeps the task
    from completing, and the agent stalls (seen live with other_insurer)."""
    if "not_sure" in spec.choices:
        return " If they don't know, choose not_sure and move on."
    if spec.kind == "text":
        return " If they don't know or would rather not say, write \"unknown\" and move on."
    if spec.kind == "date":
        return " If they can't recall the exact date, take their best estimate; if they have no idea, skip it."
    return ""

# shared by the story and details tasks
STORY_OBJECTIVE_RULES = (
    "Gather facts only, one question at a time, and ask neutrally about what each person was doing. Never comment on "
    "fault, case strength, insurance coverage, deadlines, or what an answer means for their case. Never ask for a "
    "Social Security number, policy numbers, or medical bills; the team collects those later on a short form."
)


def guava_field(spec: intake.FieldSpec) -> guava.Field:
    """My helper, not a Guava API: builds the Guava field from the schema, with the tier deciding how it's asked."""
    return guava.Field(
        key=spec.key,
        field_type=spec.kind,
        description=f"{spec.ask} {TIER_GUIDANCE[spec.tier]}{unknown_hint(spec)}",
        choices=list(spec.choices),
        required=spec.tier == intake.CRITICAL and not spec.optional,
    )


def start_story(call: guava.Call):
    call_state(call)["task"] = "story"
    call.set_task(
        "story",
        objective=(
            "Hear what happened in the caller's own words, then fill in only the details they haven't already "
            "covered. " + STORY_OBJECTIVE_RULES
        ),
        checklist=[
            "Thank them for their patience. Invite them to tell you what happened in their own words, at their own "
            "pace. If they sound upset, let them know there's no rush.",
            guava_field(intake.NARRATIVE),
            "Thank them for walking you through it, and let them know you have a few questions so the attorney has "
            "the full picture. Use their own words for what happened. For anything they already mentioned, briefly "
            "confirm it instead of asking again.",
            *[guava_field(spec) for spec in intake.CORE],
        ],
    )


def start_details(call: guava.Call, task_id: str, specs: tuple[intake.FieldSpec, ...]):
    """The case-type module: the same conversation continues, so anything already said is confirmed, not re-asked."""
    call_state(call)["task"] = task_id
    call.set_task(
        task_id,
        objective=(
            "Fill in the remaining details for this kind of case, confirming anything the caller already said "
            "instead of asking again. " + STORY_OBJECTIVE_RULES
        ),
        checklist=[
            *[guava_field(spec) for spec in specs],
            "Briefly recap what happened, their injuries, and their treatment in a sentence or two, and ask if "
            "anything needs correcting.",
        ],
    )


@agent.on_validate("first_treatment_date")
def validate_first_treatment_date(call: guava.Call, value) -> bool | tuple[bool, str]:
    if value is None:
        return True  # optional: no treatment yet
    treated = qualification.as_date(value)
    if treated is None:
        return (False, "The first treatment date wasn't a valid date. Ask the caller for it again.")
    if treated > date.today():
        return (False, "The first treatment date is in the future. Gently confirm the date with the caller.")
    incident = qualification.as_date(call.get_field("incident_date"))
    if incident and treated < incident:
        return (False, "The first treatment date is before the incident date. Gently confirm both dates.")
    return True


QUALIFY_FIELDS = (
    "incident_date", "incident_type", "incident_state", "treatment", "first_treatment_date", "government_involved",
    "other_vehicle", "on_the_job", "insurer_contact", "prior_similar_injury", "seat_belt",
)


@agent.on_task_complete("story")
def on_story_complete(call: guava.Call):
    """The module choice: the case type picks the details task; "other" has none and goes straight to qualify."""
    module = intake.MODULES.get(call.get_field("incident_type"))
    if module:
        start_details(call, *module)
    else:
        run_qualify(call)


def on_details_complete(call: guava.Call):
    run_qualify(call)


# every details task ends the same way
for details_task_id, _ in intake.MODULES.values():
    agent.on_task_complete(details_task_id)(on_details_complete)


def run_qualify(call: guava.Call):
    """The qualify step: attach flags for the attorney (never spoken), re-check any newly named parties, route."""
    state = call_state(call)
    state["flags"] |= qualification.flags({key: call.get_field(key) for key in QUALIFY_FIELDS}, date.today())
    logger.info("Story complete, flags=%s (session: %s)", sorted(state["flags"]), call.id)

    # the model often writes "none" rather than leaving the field empty; code decides what counts as a name
    other_parties = intake.named_parties(call.get_field("other_parties"))
    if other_parties:
        POOL.submit(run_recheck, call, other_parties)
    else:
        start_next_steps(call)


def run_recheck(call: guava.Call, other_parties: str):
    """Worker: re-checks parties first named in the story. The story is already heard, so a failed check doesn't end
    the call; it becomes a flag the attorney sees (MVP Flow Design.md, re-check failure policy)."""
    state = call_state(call)
    status = conflicts.check_conflicts([other_parties])
    state["recheck_status"] = status
    logger.info("Conflict re-check: %s (session: %s)", status, call.id)
    if status == "conflict":
        start_conflict_decline(call)
        return
    if status == "error":
        state["flags"].add("recheck_failed")
    start_next_steps(call)


# Next steps and retainer (Stages 6-7): explain what happens next, then email the signing packet (DocuSign) if the
# caller gives an address. Signing is never pushed on the call, and the attorney's countersignature after the call is
# the acceptance. Graph: NextSteps -> send (worker) -> DocumentsSent | DocumentsFollowUp -> Wrap
# (Texting the link is ready in texting.py, but Guava's number needs SMS brand and campaign registration first.)

# in signing order: the Statement must come before the contract (Rule 4-1.5(f)(4)(C))
SIGNING_PACKET = ("statement_of_client_rights", "fee_agreement", "hipaa_authorization")
CLOSING_TASKS = ("documents_sent", "documents_follow_up")

CLOSING_OFFER = (
    "Let them know that if they have any questions about the statement or the agreement before signing, an attorney "
    "can go over them. Then ask if there's anything else you can help with."
)


def start_next_steps(call: guava.Call):
    state = call_state(call)
    state["task"] = "next_steps"
    # set now: this is the outcome even if the call ends before the task reports complete
    state["disposition"] = "pending_signature"
    call.set_task(
        "next_steps",
        objective=(
            "Explain what happens next and the documents they'll receive. Don't comment on the merits of their case, "
            "and don't explain or interpret the fee agreement or the statement of rights."
        ),
        checklist=[
            "Thank them for the details, focusing on the process: they've given you what the attorney needs to review "
            "their situation. Don't say anything that sounds like an opinion on their case.",
            "Explain the next steps: an attorney will review their information, and if the firm takes the case, an "
            "attorney and team are typically assigned within about a week. In the meantime, suggest they gather any "
            "photos, the police report number, medical records, and insurance cards.",
            "Explain the documents: they'll first receive a Statement of Client's Rights, which they should read in "
            "full, then the fee agreement, and a form that lets the team request their medical records. They can sign "
            "whenever they're ready; there's no pressure. They'll also get a short form for details like their "
            "insurance policies and their doctors' contact information.",
            guava.Field(
                key="documents_email",
                field_type="text",
                description=(
                    "The email address they'd like the documents sent to. Ask them to spell it, then read it back to "
                    "confirm. If they'd rather not give one, write \"none\". Once they've confirmed it, tell them "
                    "you're sending it now and it'll take just a moment."
                ),
                required=True,
            ),
        ],
    )


@agent.on_task_complete("next_steps")
def on_next_steps_complete(call: guava.Call):
    email = esign.normalize_email(call.get_field("documents_email"))  # "none" -> None
    if email:
        POOL.submit(send_documents, call, email)
    else:
        logger.info("Documents not emailed (session: %s): declined or no usable email", call.id)
        start_documents_follow_up(call)


def send_documents(call: guava.Call, email: str):
    """Worker: build the signing packet in DocuSign from the CRM's templates, and have DocuSign email the caller its
    link (our signing page). Any failed step means the team sends the documents instead (flag documents_not_sent);
    the caller hears that, not an error."""
    state = call_state(call)
    fields = {key: call.get_field(key) for key in intake.ALL_KEYS}
    record = intake.build_record(fields, state, call.id, datetime.now().astimezone())
    name = record["caller"]["name"] or "Client"
    # the PNC has to exist before its documents status can be set; the full record replaces this at session end
    crm.upsert_pnc(call.id, name, fields.get("narrative") or "", record)

    templates = crm.fetch_templates(SIGNING_PACKET)
    envelope_id = esign.create_envelope(call.id, name, email, qualification.as_date(fields.get("incident_date")),
                                        templates) if templates else None
    link = signing_server.link_for(envelope_id) if envelope_id else None
    sent = bool(envelope_id and link) and esign.send_envelope(envelope_id or "", link or "")
    if not (templates and sent):
        logger.warning("Documents not sent (session: %s): templates=%s envelope=%s link=%s sent=%s", call.id,
                       bool(templates), bool(envelope_id), bool(link), sent)
        start_documents_follow_up(call)
        return

    documents = {
        "status": "sent",
        "envelopeId": envelope_id,
        "sentVia": "email",
        "sentTo": email,
        "sentAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "items": [doc_name for doc_name, _ in templates],
    }
    state["documents"] = documents
    crm.update_documents(call.id, documents)
    start_documents_sent(call, email)


def start_documents_sent(call: guava.Call, email: str):
    state = call_state(call)
    state["task"] = "documents_sent"
    state["next_steps_speech"] = []
    call.set_task(
        "documents_sent",
        objective="Confirm the documents email arrived, then close out. Don't explain or interpret the documents.",
        checklist=[
            f"Let them know you've just emailed a link to their documents to {email}. It comes from DocuSign, on "
            "behalf of Morgan and Morgan.",
            guava.Field(
                key="email_received",
                field_type="multiple_choice",
                choices=["yes", "not_yet"],
                question="Did that email come through?",
                description=(
                    "Whether the email arrived. If it hasn't yet, reassure them it can take a minute and might land "
                    "in spam, and that the team can resend it; choose not_yet and move on."
                ),
                required=True,
            ),
            "Let them know the link is just for them: they'll see the Statement of Client's Rights first, then the "
            "fee agreement and the medical records form. They can open it now or later, and sign whenever they're "
            "ready.",
            guava.Say(compliance.NEXT_STEPS_SCRIPT),
            CLOSING_OFFER,
        ],
    )


def start_documents_follow_up(call: guava.Call):
    """The documents weren't emailed (declined, no usable email, or a failed send): the team sends them."""
    state = call_state(call)
    state["flags"].add("documents_not_sent")
    state["task"] = "documents_follow_up"
    state["next_steps_speech"] = []
    call.set_task(
        "documents_follow_up",
        objective="Let them know how they'll get the documents, then close out. Don't explain or interpret them.",
        checklist=[
            "Let them know the team will send them the documents shortly. Don't mention any technical problem.",
            guava.Say(compliance.NEXT_STEPS_SCRIPT),
            CLOSING_OFFER,
        ],
    )


def on_closing_complete(call: guava.Call):
    state = call_state(call)
    missing = compliance.missing_phrases(" ".join(state["next_steps_speech"]), compliance.NEXT_STEPS_PHRASES)
    if missing:
        # audit only: flag for review rather than re-reading legal lines at the end of the call
        state["flags"].add("next_steps_unverified")
        logger.warning("Next-steps line not fully spoken, missing %s (session: %s)", missing, call.id)
    # the task already ends with "anything else?", so the model has usually said goodbye by now; don't repeat it
    call.hangup(final_instructions=(
        "If you haven't said goodbye yet, thank them warmly and wish them well in their recovery. "
        "If you already said goodbye, end the call without saying it again."
    ))


for closing_task_id in CLOSING_TASKS:
    agent.on_task_complete(closing_task_id)(on_closing_complete)


@agent.on_session_end
def on_session_end(call: guava.Call, event: BotSessionEnded):
    state = CALL_STATE.pop(call.id, None) or {}
    # opening audit record: what was disclosed and consented to (persisted to the CRM in the post-call stage)
    logger.info(
        "Session ended (session: %s) caller_name=%r recording_consent=%r caller_type=%s on_behalf_of=%s "
        "conflict_status=%s flags=%s disposition=%s termination=%s",
        call.id,
        call.get_field("caller_name"),
        call.get_field("recording_consent_final") or call.get_field("recording_consent"),
        call.get_field("caller_type"),
        call.get_field("on_behalf_of"),
        state.get("conflict_status"),
        sorted(state.get("flags", ())),
        state.get("disposition") or "partial_intake",
        event.termination_reason,
    )
    write_intake_record(call, state)


def write_intake_record(call: guava.Call, state: dict):
    """The intake record for attorney review: one JSON file per call, and a PNC in the intake CRM."""
    fields = {key: call.get_field(key) for key in intake.ALL_KEYS}
    record = intake.build_record(fields, state, call.id, datetime.now().astimezone())
    try:
        RECORDS_DIR.mkdir(exist_ok=True)
        path = RECORDS_DIR / f"{call.id}.json"
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        logger.info("Intake record written: %s", path)
    except OSError as exc:
        logger.error("Could not write intake record (session: %s): %s", call.id, exc)

    # PNCs are potential new clients: callers routed to other teams aren't, and a call that ended before the
    # caller gave a name has no one to follow up with
    name = record["caller"]["name"]
    if fields.get("caller_type") in (None, "new_injury_matter") and name:
        POOL.submit(crm.upsert_pnc, call.id, name, fields.get("narrative") or "", record)


# looks like it only inits logger and attaches listen channel if it's main. Suggesting maybe that this could have been a separate agent script for a runner in main?
if __name__ == "__main__":
    settings.load_env_file()  # DocuSign, signing link and SMS settings (.env at the repo root)
    logging_utils.configure_logging()
    signing_server.start()  # the page the texted link opens; ngrok exposes it

    # Run this to attach your agent to a phone number. Call your agent's number to talk to it.
    agent.listen_phone("+14843040566")

    # Run this to talk to your agent using your local audio device.
    # agent.call_local()

    # Run this to receive a WebRTC link where you can talk to your agent in the browser.
    # agent.listen_webrtc()

    # Run this to test your agent in a text-based chat session in the terminal (no audio required).
    # agent.chat()
