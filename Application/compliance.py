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

# read verbatim when the conflict check can't be reached the first time; the caller chooses whether to retry
CONFLICT_ERROR_SCRIPT = (
    "I'm so sorry, but I'm having trouble accessing our conflict-of-interest records right now. "
    "I can try the lookup one more time, but if it doesn't go through, unfortunately I won't be able to "
    "finish your consultation today. Would you like me to try again?"
)

# final instructions when the check can't be completed (caller declined the retry, or the retry failed too)
CONFLICT_FAILED_INSTRUCTIONS = (
    "Apologize sincerely that you weren't able to complete the check today, and explain that you'll need to end "
    "the call here. Let them know they're welcome to call back a little later, or reach Morgan and Morgan through "
    "the contact form at forthepeople.com. Thank them for their patience and wish them well in their recovery."
)

# read verbatim when the check finds a conflict (Rule 4-1.6): explain the kind of reason first, never who or what
# it involves; then the generic time-limit warning without computing any deadline, and a referral
CONFLICT_DECLINE_SCRIPT = (
    "Lawyers have strict rules about conflicts of interest. When the firm already has a connection to someone "
    "involved in a matter, we aren't allowed to take it on, and I'm not able to share the details of that "
    "connection. Because of that, I'm truly sorry, but Morgan and Morgan won't be able to represent you in this "
    "matter. Please don't let that stop you from getting help: there are time limits on injury claims, so I'd "
    "encourage you to speak with another attorney soon. The Florida Bar's Lawyer Referral Service can help you "
    "find one at 800-342-8011."
)

# final instructions when the caller already has a lawyer for this matter (Rule 4-4.2: an attorney decides)
REPRESENTED_INSTRUCTIONS = (
    "Thank them for letting you know. Explain that since they already have a lawyer for this matter, one of the "
    "firm's attorneys will need to speak with them directly, and that an attorney will reach out to them. "
    "Don't ask any more questions about the case, then say goodbye warmly."
)

# read verbatim at next steps: an attorney decides (RF 3), the agreement is final only once both sign
# (Rule 4-1.5(f)(2)), and the mandatory 3-business-day cancellation right (4-1.5(f)(4)(A)(ii)), stated, not interpreted
NEXT_STEPS_SCRIPT = (
    "An attorney will review everything and decide whether the firm can take your case; the agreement is only "
    "final once both you and a Morgan and Morgan attorney have signed it. It also gives you three business days "
    "after signing to cancel in writing."
)
NEXT_STEPS_PHRASES = ("decide", "final", "three business days")

# approved answer to any question about fees or whether to sign (Op. 88-6: intake never interprets the agreement)
FEE_ANSWER = (
    "That's a great question for an attorney. An attorney can go over the agreement and any questions about fees "
    "with you before you sign anything."
)

# how the FAQ lookup (Guava DocumentQA over firm-faq.md) may answer: the FAQ only, nothing advisory (Op. 88-6)
FAQ_INSTRUCTIONS = (
    "You answer questions from people calling a law firm's intake line. Answer in one or two short, warm sentences, "
    "using only the FAQ. If the FAQ doesn't cover the question, say you're not sure and that the team will follow up. "
    "Never give legal or medical advice, and never give an opinion on fault, case strength, or case value."
)

# when the FAQ can't be reached: something a caller can hear, never a technical error
FAQ_FALLBACK = "I'm not sure about that one, but I'll make sure the team follows up with you on it."

FEE_QUESTION_WORDS =("fee", "percent", "cost", "charge", "pay you", "should i sign", "contract", "agreement")

# phrases that must appear in the agent's actual speech for the disclosures to count as delivered
REQUIRED_PHRASES = ("not a lawyer", "employee", "legal advice", "recorded")


def _normalize(text: str) -> str:
    text = re.sub(r"[^a-z0-9' ]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def is_recording_question(question: str) -> bool:
    return "record" in question.lower()


def is_fee_question(question: str) -> bool:
    lowered = question.lower()
    return any(word in lowered for word in FEE_QUESTION_WORDS)


def missing_phrases(spoken: str, required: tuple[str, ...]) -> list[str]:
    """Return the required phrases that do not appear in what the agent said."""
    normalized = _normalize(spoken)
    return [phrase for phrase in required if phrase not in normalized]


def missing_disclosure_phrases(spoken: str) -> list[str]:
    return missing_phrases(spoken, REQUIRED_PHRASES)
