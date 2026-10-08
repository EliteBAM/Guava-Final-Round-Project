"""
DocuSign client (developer sandbox) for the signing packet: one envelope per call, client first, attorney second.

The client is an embedded signer (clientUserId = the Guava call ID) with an embeddedRecipientStartURL: DocuSign
emails them an invitation whose button opens our signing page (signing_server.py), which starts a fresh DocuSign
session on every visit. The start URL holds the envelope ID, so the envelope is created as a draft, given the URL,
then sent. The attorney is a normal signer, so DocuSign emails them once the client has signed.

Login is DocuSign's JWT grant (impersonating the app's own user); everything else is plain REST. Every function
returns a value, or None / False on failure, and never raises. Logs never contain names.

Fields are placed by the hidden anchors in the Assets/ templates: see "Documents and Data Stack.md", section 2.

    python -m esign --consent-url    print the one-time consent link
    python -m esign you@example.com  sandbox dry run: emails you a test envelope and serves the signing page
"""

import base64
import http.client
import json
import logging
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

import jwt

import settings

logger = logging.getLogger("guava.intro_agent")

AUTH_SERVER = "account-d.docusign.com"  # the developer sandbox
SCOPES = "signature impersonation"
CONSENT_REDIRECT = "http://localhost:3001/consent"
REQUIRED = ("DOCUSIGN_INTEGRATION_KEY", "DOCUSIGN_USER_ID", "DOCUSIGN_ACCOUNT_ID", "ATTORNEY_NAME", "ATTORNEY_EMAIL")
EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[a-z]{2,}")

# Tab positions relative to each anchor, in pixels. Anchors sit at the left of the line, just above it; tuned in
# the sandbox dry run.
TEXT_OFFSET = {"anchorXOffset": "0", "anchorYOffset": "-4"}
SIGN_OFFSET = {"anchorXOffset": "0", "anchorYOffset": "-28"}


def configured() -> bool:
    return all(os.environ.get(name) for name in REQUIRED) and private_key_path().is_file()


def private_key_path():
    return settings.repo_path(os.environ.get("DOCUSIGN_PRIVATE_KEY_PATH", "Application/docusign_private.key"))


def private_key() -> str:
    """The PEM text. A key pasted without its BEGIN/END lines is wrapped (DocuSign's keys are PKCS#1 RSA)."""
    text = private_key_path().read_text(encoding="utf-8").strip()
    if "-----BEGIN" in text:
        return text
    body = "".join(text.split())
    lines = [body[i:i + 64] for i in range(0, len(body), 64)]
    return "\n".join(["-----BEGIN RSA PRIVATE KEY-----", *lines, "-----END RSA PRIVATE KEY-----", ""])


def normalize_email(text: str | None) -> str | None:
    """The caller's email as the agent wrote it down, or None for "none" and anything that isn't an address."""
    email = "".join((text or "").split()).lower()
    return email if EMAIL.fullmatch(email) else None


def consent_url() -> str:
    query = urllib.parse.urlencode({
        "response_type": "code", "scope": SCOPES,
        "client_id": os.environ.get("DOCUSIGN_INTEGRATION_KEY", ""), "redirect_uri": CONSENT_REDIRECT,
    })
    return f"https://{AUTH_SERVER}/oauth/auth?{query}"


# ---------------------------------------------------------------- envelope (pure)

def _anchor(anchor: str, offset: dict, **extra) -> dict:
    return {"anchorString": anchor, "anchorUnits": "pixels", "anchorIgnoreIfNotPresent": "true", **offset, **extra}


def _locked_text(anchor: str, label: str, value: str, width: int = 220) -> dict:
    return _anchor(anchor, TEXT_OFFSET, tabLabel=label, value=value, locked="true", width=str(width),
                   font="helvetica", fontSize="size10")


def client_tabs(client_name: str, incident_date: date | None, today: date) -> dict:
    return {
        "textTabs": [
            _locked_text("\\c_name\\", "client_name", client_name),
            _locked_text("\\i_date\\", "incident_date", f"{incident_date:%B %d, %Y}" if incident_date else ""),
            _locked_text("\\s_date\\", "prepared_date", f"{today:%B %d, %Y}", width=140),
            _anchor("\\c_dob\\", TEXT_OFFSET, tabLabel="date_of_birth", required="true", width="160",
                    font="helvetica", fontSize="size10"),
        ],
        "signHereTabs": [_anchor("\\c_sign\\", SIGN_OFFSET)],
        "dateSignedTabs": [_anchor("\\c_date\\", TEXT_OFFSET, font="helvetica", fontSize="size10")],
        "initialHereTabs": [_anchor("\\c_init\\", SIGN_OFFSET, optional="true")],
    }


def attorney_tabs() -> dict:
    return {
        "signHereTabs": [_anchor("\\a_sign\\", SIGN_OFFSET)],
        "fullNameTabs": [_anchor("\\a_name\\", TEXT_OFFSET, font="helvetica", fontSize="size10")],
        "dateSignedTabs": [_anchor("\\a_date\\", TEXT_OFFSET, font="helvetica", fontSize="size10")],
    }


def envelope_definition(call_id: str, client_name: str, client_email: str, incident_date: date | None,
                        documents: list[tuple[str, bytes]], today: date) -> dict:
    """documents are (name, pdf) in signing order: the Statement must come first. A draft: send_envelope sends it."""
    return {
        "emailSubject": "Morgan and Morgan: documents to review and sign",
        "emailBlurb": ("Here are your documents to review. Sign whenever you're ready; an attorney can answer any "
                       "questions before you sign. Sample documents for a software demonstration."),
        "documents": [
            {"documentId": str(i), "name": name, "fileExtension": "pdf",
             "documentBase64": base64.b64encode(pdf).decode()}
            for i, (name, pdf) in enumerate(documents, 1)
        ],
        "recipients": {"signers": [
            # clientUserId makes the client an embedded signer, so signing goes through our page (send_envelope
            # sets the start URL that makes DocuSign email them anyway)
            {"recipientId": "1", "routingOrder": "1", "name": client_name, "email": client_email,
             "clientUserId": call_id, "tabs": client_tabs(client_name, incident_date, today)},
            {"recipientId": "2", "routingOrder": "2", "name": os.environ.get("ATTORNEY_NAME", ""),
             "email": os.environ.get("ATTORNEY_EMAIL", ""), "tabs": attorney_tabs()},
        ]},
        "status": "created",
    }


# ---------------------------------------------------------------- REST

_session_lock = threading.Lock()
_session: dict = {"token": "", "expires": 0.0, "base": ""}


def _call(method: str, url: str, *, token: str = "", body: dict | None = None, form: dict | None = None) -> dict:
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    elif form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read() or b"{}")


def _account() -> tuple[str, str]:
    """(access token, account REST base), refreshed five minutes before the token expires."""
    with _session_lock:
        if _session["token"] and time.time() < _session["expires"] - 300:
            return _session["token"], _session["base"]
        now = int(time.time())
        assertion = jwt.encode(
            {"iss": os.environ["DOCUSIGN_INTEGRATION_KEY"], "sub": os.environ["DOCUSIGN_USER_ID"],
             "aud": AUTH_SERVER, "iat": now, "exp": now + 3600, "scope": SCOPES},
            private_key(), algorithm="RS256",
        )
        grant = _call("POST", f"https://{AUTH_SERVER}/oauth/token",
                      form={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion})
        token = grant["access_token"]
        account_id = os.environ["DOCUSIGN_ACCOUNT_ID"]
        info = _call("GET", f"https://{AUTH_SERVER}/oauth/userinfo", token=token)
        account = next(a for a in info["accounts"] if a["account_id"] == account_id)
        base = f"{account['base_uri']}/restapi/v2.1/accounts/{account_id}"
        _session.update(token=token, expires=now + int(grant.get("expires_in", 3600)), base=base)
        return token, base


def _failure(action: str, exc: Exception) -> None:
    """Logs DocuSign's error code (e.g. consent_required), never the request, which holds the client's name."""
    detail = ""
    if isinstance(exc, urllib.error.HTTPError):
        try:
            payload = json.loads(exc.read() or b"{}")
            detail = payload.get("errorCode") or payload.get("error") or ""
        except ValueError:
            pass
        detail = f"{exc.code} {detail}".strip()
    logger.warning("DocuSign %s failed: %s %s", action, type(exc).__name__, detail)


# OSError covers URLError, HTTPError and timeouts; the rest are bad keys, bad JSON, or an unexpected response
FAILURES = (OSError, http.client.HTTPException, ValueError, KeyError, StopIteration, jwt.PyJWTError)


def create_envelope(call_id: str, client_name: str, client_email: str, incident_date: date | None,
                    documents: list[tuple[str, bytes]]) -> str | None:
    """The draft envelope's ID. Nothing is emailed until send_envelope."""
    if not configured():
        logger.warning("DocuSign isn't configured (see .env): no envelope created")
        return None
    try:
        token, base = _account()
        created = _call("POST", f"{base}/envelopes", token=token, body=envelope_definition(
            call_id, client_name, client_email, incident_date, documents, date.today()))
        return created["envelopeId"]
    except FAILURES as exc:
        _failure("create envelope", exc)
        return None


def send_envelope(envelope_id: str, start_url: str) -> bool:
    """Points the client's invitation email at our signing page (start_url), then sends: DocuSign emails them now."""
    try:
        token, base = _account()
        envelope = f"{base}/envelopes/{urllib.parse.quote(envelope_id)}"
        signer = _embedded_signer(token, base, envelope_id)
        _call("PUT", f"{envelope}/recipients", token=token, body={"signers": [{
            "recipientId": signer["recipientId"], "name": signer["name"], "email": signer["email"],
            "clientUserId": signer["clientUserId"], "embeddedRecipientStartURL": start_url,
        }]})
        _call("PUT", envelope, token=token, body={"status": "sent"})
        return True
    except FAILURES as exc:
        _failure("send envelope", exc)
        return False


def _embedded_signer(token: str, base: str, envelope_id: str) -> dict:
    recipients = _call("GET", f"{base}/envelopes/{urllib.parse.quote(envelope_id)}/recipients", token=token)
    return next(s for s in recipients["signers"] if s.get("clientUserId"))


def signing_url(envelope_id: str, return_url: str) -> str | None:
    """A fresh signing session for the client. DocuSign's URL works once and expires within minutes."""
    try:
        token, base = _account()
        signer = _embedded_signer(token, base, envelope_id)
        view = _call("POST", f"{base}/envelopes/{urllib.parse.quote(envelope_id)}/views/recipient", token=token,
                     body={"returnUrl": return_url, "authenticationMethod": "none", "email": signer["email"],
                           "userName": signer["name"], "clientUserId": signer["clientUserId"]})
        return view["url"]
    except FAILURES as exc:
        _failure("signing session", exc)
        return None


def client_signed(envelope_id: str) -> str | None:
    """The call ID (the client's clientUserId) once the client has signed, otherwise None."""
    try:
        token, base = _account()
        signer = _embedded_signer(token, base, envelope_id)
        return signer["clientUserId"] if signer.get("status") == "completed" else None
    except FAILURES as exc:
        _failure("status check", exc)
        return None


# ---------------------------------------------------------------- command line

def _dry_run(email: str) -> None:
    """Emails a test envelope from the Assets/ PDFs, and serves the signing page its button opens (through ngrok)."""
    import signing_server  # it imports this module, so not at the top

    assets = settings.REPO_ROOT / "Assets"
    documents = [(name, (assets / f"{stem}.pdf").read_bytes()) for name, stem in (
        ("Statement of Client’s Rights", "statement-of-client-rights"),
        ("Contingency Fee Agreement", "contingency-fee-agreement"),
        ("HIPAA Authorization", "hipaa-authorization"),
    )]
    call_id = f"dryrun-{int(time.time())}"
    envelope_id = create_envelope(call_id, "Test Client", email, date(2026, 9, 30), documents)
    if not envelope_id:
        print("No envelope: see the warning above. If it says consent_required, open:\n" + consent_url())
        return
    link = signing_server.link_for(envelope_id)
    if not (link and send_envelope(envelope_id, link)):
        print("Envelope", envelope_id, "was created but not sent: see the warning above.")
        return
    signing_server.start()
    print("Envelope:", envelope_id)
    input(f"Sent to {email}. Check your email (ngrok must be running), sign, then press Enter to stop. ")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings.load_env_file()
    email = normalize_email(sys.argv[1]) if len(sys.argv) > 1 else None
    if "--consent-url" in sys.argv:
        print(consent_url())
    elif email:
        _dry_run(email)
    else:
        sys.exit("usage: python -m esign you@example.com   (or --consent-url)")
