"""
Firm-approved compliance wording and the code-side check that it was actually spoken.

Kept free of guava imports so it can be unit tested without credentials or a network.
Wording here is a draft; in production the firm's ethics counsel signs off on it.

Sources (see Documents/Legal Intake Specialist Agent Notes/Research Findings.md):
- Fla. Bar Ethics Op. 24-1: tell prospects they are talking to an AI, not a lawyer or firm employee.
- Fla. Bar Ethics Op. 88-6: intake identifies as a nonlawyer, gathers facts only, gives no legal advice.
- Rule 4-1.18 comment: cautionary statement that limits the firm's obligations.
- Fla. Stat. 934.03: all-party consent to record the call.
"""

import re

# read verbatim (guava.Say) in the disclosures task
DISCLOSURE_SCRIPT = (
    "I'm an AI, not a lawyer and not a Morgan and Morgan employee, so I can't give legal advice. "
    "My job is to gather the facts and pass them to our attorneys, who decide whether the firm can help. "
    "Speaking with me doesn't by itself make Morgan and Morgan your lawyer. "
    "This call is recorded so the attorney reviewing it has an accurate record."
)

# the one truthful reason the call is recorded; every explanation of recording uses this wording
RECORDING_REASON = (
    "We record calls so the attorney who reviews your situation has an accurate record of what you told us. "
    "The recording is kept confidential."
)

# canonical answer to any question about the recording (returned from on_question in code)
RECORDING_ANSWER = RECORDING_REASON + " I'm not able to turn the recording off on this line."

# persona rule, so the model doesn't improvise reasons when it answers on its own
RECORDING_POLICY = (
    f"If the caller asks a question about the call recording, answer only with: \"{RECORDING_ANSWER}\" "
    "Never give any other reason for recording, such as quality assurance, training, or a legal requirement. "
    "If the caller declines recording, do not explain, persuade, or end the call yourself; "
    "just record their answer, because declining is handled in its own step."
)

# field guidance for every consent question: a "no" is a complete answer, not an objection to overcome
CONSENT_FIELD_GUIDANCE = (
    "If the caller says no or that they don't want to be recorded, record that answer right away. "
    "Do not explain the recording, re-ask, or try to change their mind."
)

# read verbatim if the caller declines recording the first time: truthful reason plus a clear warning
CONSENT_RECONSIDER_SCRIPT = (
    "I understand. " + RECORDING_REASON + " "
    "If you'd still prefer not to be recorded, I'll have to end our call, but you can always reach "
    "Morgan and Morgan through the contact form at forthepeople.com. "
    "Are you sure you'd prefer not to be recorded?"
)

# final instructions for the soft hangup after a second decline
CONSENT_DECLINED_INSTRUCTIONS = (
    "Thank the caller sincerely and explain that you can't continue the call without their consent to record. "
    "Let them know they can still reach Morgan and Morgan through the contact form at forthepeople.com. "
    "Do not ask them any further questions."
)

# read verbatim to insurance adjusters and other parties' lawyers (Rule 4-1.6): never confirm or deny a client
CONFIDENTIALITY_SCRIPT = (
    "I'm not able to confirm whether anyone is a client of the firm or discuss any case, "
    "but I'll have the right team reach out to you."
)

# phrases that must appear in the agent's actual speech for the disclosures to count as delivered
REQUIRED_PHRASES = ("not a lawyer", "employee", "legal advice", "recorded")


def _normalize(text: str) -> str:
    text = re.sub(r"[^a-z0-9' ]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def is_recording_question(question: str) -> bool:
    return "record" in question.lower()


def missing_disclosure_phrases(spoken: str) -> list[str]:
    """Return the REQUIRED_PHRASES that do not appear in what the agent said."""
    normalized = _normalize(spoken)
    return [phrase for phrase in REQUIRED_PHRASES if phrase not in normalized]
