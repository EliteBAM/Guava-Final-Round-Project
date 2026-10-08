"""
Texting the caller their documents link, through Guava's SMS API (guava.Client().send_sms).

Not used by the call yet: Guava refuses SMS until the number's SMS brand and campaign registration is approved, so
DocuSign emails the link instead (main.send_documents). `python -m texting +1XXXXXXXXXX` checks whether texting works.
Nothing is sent unless SMS_ENABLED=1 (set in .env, which tests never load).
"""

import logging
import os
import re

import guava
import httpx

logger = logging.getLogger("guava.intro_agent")

# no case details: texts aren't secure. Identifies the firm and gives STOP, as A2P 10DLC registration expects.
MESSAGE = (
    "Morgan and Morgan: here are your documents to review, and sign whenever you're ready: {link} "
    "An attorney can answer any questions before you sign. Reply STOP to opt out."
)


def normalize_us_number(text: str | None) -> str | None:
    """+1XXXXXXXXXX from a caller ID or a spoken number ("(407) 555-0123"), or None if it isn't a US number."""
    digits = re.sub(r"\D", "", text or "")
    if len(digits) == 10:
        return "+1" + digits
    if len(digits) == 11 and digits.startswith("1"):
        return "+" + digits
    return None


def last4(number: str) -> str:
    return number[-4:]


def spoken_last4(number: str) -> str:
    """Digit by digit, so it isn't read as "four thousand five hundred..."."""
    return ", ".join(last4(number))


def send_documents_text(from_number: str, to_number: str, link: str) -> str:
    """ "ok", "disabled" or "error"."""
    if os.environ.get("SMS_ENABLED") != "1":
        logger.info("SMS is disabled (SMS_ENABLED isn't 1): the documents link wasn't texted")
        return "disabled"
    try:
        guava.Client().send_sms(from_number=from_number, to_number=to_number, message=MESSAGE.format(link=link))
        return "ok"
    # the SDK raises its own and httpx's errors; the link stays out of the log
    except httpx.HTTPStatusError as exc:
        # Guava's reply says why (e.g. the number can't send texts)
        logger.warning("SMS send failed: HTTP %s %s", exc.response.status_code,
                       exc.response.text.replace(link, "<link>")[:300])
        return "error"
    except Exception as exc:
        logger.warning("SMS send failed: %s %s", type(exc).__name__, str(exc).replace(link, "<link>")[:300])
        return "error"


if __name__ == "__main__":
    # one test text without a call:  python -m texting +1XXXXXXXXXX
    import sys

    import settings

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings.load_env_file()
    to = normalize_us_number(sys.argv[1] if len(sys.argv) > 1 else None)
    if not to:
        sys.exit("usage: python -m texting <US mobile number>")
    sender = os.environ.get("GUAVA_AGENT_NUMBER") or "+14843040566"
    print(send_documents_text(sender, to, "https://example.com/test"))
