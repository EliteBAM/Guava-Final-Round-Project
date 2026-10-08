"""
Client for the firm's conflict-of-interest check.

Every outcome is normalized to "clear", "conflict" or "error". Timeouts, HTTP errors, malformed JSON and
unexpected values all become "error", so the conversation only ever branches on those three, and the
model never sees raw API output.
"""

import http.client
import json
import logging
import os
import urllib.request

logger = logging.getLogger("guava.intro_agent")

CONFLICT_STATUSES = ("clear", "conflict")


def api_url() -> str:
    return os.environ.get("CONFLICT_API_URL", "http://127.0.0.1:8787")


def check_conflicts(names: list[str], timeout: float = 5.0) -> str:
    request = urllib.request.Request(
        f"{api_url()}/conflicts/check",
        data=json.dumps({"names": names}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = json.loads(response.read()).get("status")
    # OSError covers URLError, HTTPError, timeouts and refused connections; ValueError covers bad JSON;
    # AttributeError covers JSON that isn't an object
    except (OSError, http.client.HTTPException, ValueError, AttributeError) as exc:
        # names are deliberately not logged: they're a prospective client's confidential information
        logger.warning("Conflict check failed: %s", type(exc).__name__)
        return "error"

    if status not in CONFLICT_STATUSES:
        logger.warning("Conflict check returned an unexpected status")
        return "error"
    return status
