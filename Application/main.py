"""
Guava Legal Intake Specialist Agent taylored for Morgan and Morgan injury law firm on-spec.
Engineer: Robert Gehr 10-07-2026
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import guava
from guava import logging_utils
from guava.events import AgentSpeechEvent, BotSessionEnded
from guava.helpers.rag import DocumentQA

import compliance
import conflicts
import qualification
import timezones

logger = logging.getLogger("guava.intro_agent")

CURRENT_DIR = Path(__file__).resolve().parent

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
    elif state["task"] == "next_steps":
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


# Story: the caller's account in their own words, then only the details still missing. One Guava task: the model
# fills fields from what the caller already said and asks only the gaps (MVP Flow Design.md, Stage 4).
# Graph: Story -> qualify -> DeclineConflict | NextSteps

def start_story(call: guava.Call):
    call_state(call)["task"] = "story"
    call.set_task(
        "story",
        objective=(
            "Hear what happened in the caller's own words, then fill in only the details they haven't already "
            "covered. Never comment on fault, case strength, or what the case might be worth."
        ),
        checklist=[
            "Thank them for their patience. Invite them to tell you what happened in their own words, at their own pace.",
            guava.Field(
                key="narrative",
                field_type="text",
                description=(
                    "Their account of what happened. Let them finish before asking anything else, "
                    "and acknowledge any injuries with care."
                ),
                required=True,
            ),
            "Thank them for walking you through it, and let them know you have a few quick questions. For anything "
            "they already mentioned, briefly confirm it instead of asking again.",
            guava.Field(
                key="incident_type",
                field_type="multiple_choice",
                choices=["motor_vehicle", "slip_and_fall", "medical_or_nursing_home", "other"],
                description="What kind of incident it was.",
                required=True,
            ),
            guava.Field(
                key="incident_state",
                field_type="multiple_choice",
                choices=["florida", "other_state"],
                description="Whether it happened in Florida or another state.",
                required=True,
            ),
            guava.Field(
                key="incident_location",
                field_type="text",
                description="The city or county where it happened.",
                required=False,
            ),
            guava.Field(key="injuries", field_type="text", description="Their injuries.", required=True),
            guava.Field(
                key="treatment",
                field_type="multiple_choice",
                choices=["er_or_hospital", "doctor_or_urgent_care", "none_yet"],
                description="The medical care they've had so far, if any.",
                required=True,
            ),
            guava.Field(
                key="first_treatment_date",
                field_type="date",
                description="The date they were first treated. Only ask if they've had treatment.",
                required=False,
            ),
            guava.Field(
                key="vehicle_role",
                field_type="multiple_choice",
                choices=["driver", "passenger", "pedestrian", "cyclist", "motorcyclist", "not_applicable"],
                description=(
                    "Their role in the vehicle accident. If it wasn't a vehicle accident, choose not_applicable "
                    "without asking."
                ),
                required=True,
            ),
            guava.Field(
                key="police_report",
                field_type="multiple_choice",
                choices=["yes", "no", "not_sure"],
                description="Whether a police report was made.",
                required=True,
            ),
            guava.Field(
                key="government_involved",
                field_type="multiple_choice",
                choices=["yes", "no", "not_sure"],
                description=(
                    "Whether a government vehicle or property was involved, such as a city bus, police car, "
                    "or public property."
                ),
                required=True,
            ),
            guava.Field(
                key="other_insurer",
                field_type="text",
                description="The other party's insurance company, if they know it.",
                required=False,
            ),
            guava.Field(
                key="other_parties",
                field_type="text",
                description=(
                    "Anyone else involved whom they haven't already named, such as the other driver's employer or a "
                    "business. It's fine if there's no one."
                ),
                required=False,
            ),
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
)


@agent.on_task_complete("story")
def on_story_complete(call: guava.Call):
    """The qualify step: attach flags for the attorney (never spoken), re-check any newly named parties, route."""
    state = call_state(call)
    state["flags"] |= qualification.flags({key: call.get_field(key) for key in QUALIFY_FIELDS}, date.today())
    logger.info("Story complete, flags=%s (session: %s)", sorted(state["flags"]), call.id)

    other_parties = (call.get_field("other_parties") or "").strip()
    if other_parties:
        POOL.submit(run_recheck, call, other_parties)
    else:
        start_next_steps(call)


def run_recheck(call: guava.Call, other_parties: str):
    """Worker: re-checks parties first named in the story. The story is already heard, so a failed check doesn't end
    the call; it becomes a flag the attorney sees (MVP Flow Design.md, re-check failure policy)."""
    state = call_state(call)
    status = conflicts.check_conflicts([other_parties])
    logger.info("Conflict re-check: %s (session: %s)", status, call.id)
    if status == "conflict":
        start_conflict_decline(call)
        return
    if status == "error":
        state["flags"].add("recheck_failed")
    start_next_steps(call)


# Next steps and retainer (Stage 6): explain what happens next and the documents. Nothing is sent on this call yet,
# and the attorney's countersignature after the call is the acceptance.

def start_next_steps(call: guava.Call):
    state = call_state(call)
    state["task"] = "next_steps"
    state["next_steps_speech"] = []
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
            "full, and then the fee agreement, which they can sign whenever they're ready. There's no pressure.",
            guava.Say(compliance.NEXT_STEPS_SCRIPT),
            "Let them know that if they have any questions about the statement or the agreement before signing, an "
            "attorney can go over them. Then ask if there's anything else you can help with.",
        ],
    )


@agent.on_task_complete("next_steps")
def on_next_steps_complete(call: guava.Call):
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


# looks like it only inits logger and attaches listen channel if it's main. Suggesting maybe that this could have been a separate agent script for a runner in main?
if __name__ == "__main__":
    logging_utils.configure_logging()

    # Run this to attach your agent to a phone number. Call your agent's number to talk to it.
    agent.listen_phone("+14843040566")

    # Run this to talk to your agent using your local audio device.
    # agent.call_local()

    # Run this to receive a WebRTC link where you can talk to your agent in the browser.
    # agent.listen_webrtc()

    # Run this to test your agent in a text-based chat session in the terminal (no audio required).
    # agent.chat()
