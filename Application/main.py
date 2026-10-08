"""
Guava Legal Intake Specialist Agent taylored for Morgan and Morgan injury law firm on-spec.
Engineer: Robert Gehr 10-07-2026
"""

import logging
from pathlib import Path

import guava
from guava import logging_utils
from guava.events import AgentSpeechEvent, BotSessionEnded
from guava.helpers.rag import DocumentQA

import compliance
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

# tasks during which the agent's speech is captured for the disclosure check
DISCLOSURE_TASKS = ("disclosures", "consent_reconsider")


def call_state(call: guava.Call) -> dict:
    return CALL_STATE.setdefault(call.id, {
        "task": None,
        "disclosure_speech": [],
        "disclosure_retries": 0,
        "flags": set(),
        "disposition": None,
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
        # placeholder until the conflict screen is built
        call.hangup(final_instructions="Thank them, and let them know a member of the intake team will follow up shortly.")
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


@agent.on_session_end
def on_session_end(call: guava.Call, event: BotSessionEnded):
    state = CALL_STATE.pop(call.id, None) or {}
    # opening audit record: what was disclosed and consented to (persisted to the CRM in the post-call stage)
    logger.info(
        "Session ended (session: %s) caller_name=%r recording_consent=%r caller_type=%s on_behalf_of=%s "
        "flags=%s disposition=%s termination=%s",
        call.id,
        call.get_field("caller_name"),
        call.get_field("recording_consent_final") or call.get_field("recording_consent"),
        call.get_field("caller_type"),
        call.get_field("on_behalf_of"),
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
