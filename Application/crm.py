"""
Client for the intake CRM (the mock in "Intake CRM/"): sends each call's intake record as a PNC (potential new client).

The PUT is keyed on the Guava call ID, so sending the same call again updates its PNC instead of duplicating it.
Every outcome is "ok" or "error". It runs after the call has ended, so a failure is logged and nothing else.
API: Intake CRM/Documents/2-API.md.
"""

import http.client
import json
import logging
import os
import urllib.parse
import urllib.request
from pathlib import Path

logger = logging.getLogger("guava.intro_agent")

# the CRM writes its API key here the first time it starts
KEY_FILE = Path(__file__).resolve().parent.parent / "Intake CRM" / "data" / "api-key.txt"
MAX_NAME, MAX_SUMMARY = 200, 5000  # the CRM's limits


def api_url() -> str:
    return os.environ.get("CRM_API_URL", "http://127.0.0.1:3000/api/v1")


def api_key() -> str:
    key = os.environ.get("CRM_API_KEY")
    if key:
        return key
    try:
        return KEY_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def upsert_pnc(call_id: str, name: str, summary: str, record: dict, timeout: float = 5.0) -> str:
    request = urllib.request.Request(
        f"{api_url()}/pncs/{urllib.parse.quote(call_id, safe='')}",
        data=json.dumps({"name": name[:MAX_NAME], "summary": summary[:MAX_SUMMARY], "record": record}).encode(),
        headers={"Content-Type": "application/json", "X-API-Key": api_key()},
        method="PUT",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout):
            return "ok"
    # OSError covers URLError, HTTPError, timeouts and refused connections
    except (OSError, http.client.HTTPException) as exc:
        # the record is the caller's confidential information: log only what failed
        logger.warning("CRM update failed (session: %s): %s %s", call_id, type(exc).__name__, getattr(exc, "code", ""))
        return "error"
