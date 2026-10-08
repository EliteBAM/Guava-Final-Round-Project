"""
Client for the intake CRM (the mock in "Intake CRM/"): PNC (potential new client) records and document templates.

- upsert_pnc: the call's intake record, keyed on the Guava call ID, so sending the same call again updates its PNC
  instead of duplicating it.
- fetch_templates: the signing-packet PDFs, found by kind (e.g. "fee_agreement").
- update_documents: the signing packet's status on the PNC (sent, client_signed).

Every outcome is a value or "error" / None, and nothing raises. API: Intake CRM/Documents/2-API.md.
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

# OSError covers URLError, HTTPError, timeouts and refused connections; ValueError covers bad JSON
FAILURES = (OSError, http.client.HTTPException, ValueError)


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


def _send(method: str, path: str, body: dict | None = None, timeout: float = 5.0) -> bytes:
    headers = {"X-API-Key": api_key()}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(f"{api_url()}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _pnc_path(call_id: str) -> str:
    return f"/pncs/{urllib.parse.quote(call_id, safe='')}"


def _failure(action: str, call_id: str, exc: Exception) -> None:
    # records are the caller's confidential information: log only what failed
    logger.warning("CRM %s failed (session: %s): %s %s", action, call_id, type(exc).__name__, getattr(exc, "code", ""))


def upsert_pnc(call_id: str, name: str, summary: str, record: dict, timeout: float = 5.0) -> str:
    body = {"name": name[:MAX_NAME], "summary": summary[:MAX_SUMMARY], "record": record}
    try:
        _send("PUT", _pnc_path(call_id), body, timeout)
        return "ok"
    except FAILURES as exc:
        _failure("update", call_id, exc)
        return "error"


def update_documents(call_id: str, documents: dict, timeout: float = 5.0) -> str:
    """Merges into the PNC's documents status. The PNC must already exist (upsert_pnc first)."""
    try:
        _send("PATCH", f"{_pnc_path(call_id)}/documents", documents, timeout)
        return "ok"
    except FAILURES as exc:
        _failure("documents update", call_id, exc)
        return "error"


def fetch_templates(kinds: tuple[str, ...], timeout: float = 10.0) -> list[tuple[str, bytes]] | None:
    """(name, pdf) for each kind, in the order given, or None if any is missing or the CRM can't be reached."""
    try:
        by_kind = {doc.get("kind"): doc for doc in json.loads(_send("GET", "/documents", timeout=timeout))}
        missing = [kind for kind in kinds if kind not in by_kind]
        if missing:
            logger.warning("CRM library is missing templates %s: run `npm run seed` in Intake CRM", missing)
            return None
        return [(by_kind[kind]["name"], _send("GET", f"/documents/{urllib.parse.quote(by_kind[kind]['id'])}",
                                              timeout=timeout)) for kind in kinds]
    except FAILURES + (KeyError, TypeError, AttributeError) as exc:
        _failure("template fetch", "-", exc)
        return None
