"""
The page behind the link in DocuSign's email: it turns a long-lived link into a fresh DocuSign signing session on
each visit.

DocuSign's own signing URLs work once and expire within minutes, so the email carries our link instead:
    {SIGNING_PUBLIC_URL}/sign/{envelope_id}/{signature}
The signature is an HMAC of the envelope ID with SIGNING_SECRET, so links can't be guessed, and nothing is stored:
links keep working across restarts. ngrok exposes this server (port 3001) and nothing else.

Routes:
    GET /sign/{id}/{sig}                  check the signature, then redirect to a new DocuSign session
    GET /sign/{id}/{sig}/done?event=...   DocuSign's return URL: on signing_complete, confirm with DocuSign and
                                          mark the PNC's documents "client_signed" in the CRM
"""

import hashlib
import hmac
import html
import logging
import os
import re
import threading
import urllib.parse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import crm
import esign

logger = logging.getLogger("guava.intro_agent")

PORT = 3001
ENVELOPE_ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def signature(envelope_id: str) -> str:
    secret = os.environ.get("SIGNING_SECRET", "").encode()
    return hmac.new(secret, envelope_id.encode(), hashlib.sha256).hexdigest()[:32]


def public_url() -> str:
    """The ngrok address, with https:// added if .env gives just the domain (DocuSign needs an absolute URL)."""
    url = os.environ.get("SIGNING_PUBLIC_URL", "").strip().rstrip("/")
    return url if not url or "://" in url else f"https://{url}"


def link_for(envelope_id: str) -> str | None:
    if not (public_url() and os.environ.get("SIGNING_SECRET")):
        logger.warning("SIGNING_PUBLIC_URL or SIGNING_SECRET isn't set (see .env): no signing link")
        return None
    return f"{public_url()}/sign/{envelope_id}/{signature(envelope_id)}"


def valid(envelope_id: str, sig: str) -> bool:
    return bool(ENVELOPE_ID.fullmatch(envelope_id)) and bool(os.environ.get("SIGNING_SECRET")) \
        and hmac.compare_digest(sig, signature(envelope_id))


def page(title: str, message: str, link: str = "", link_text: str = "") -> bytes:
    action = f'<p><a href="{html.escape(link)}">{html.escape(link_text)}</a></p>' if link else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>body{{margin:0;padding:48px 20px;background:#f7f8fa;color:#1b1d22;font:17px/1.55 system-ui,sans-serif}}
main{{max-width:460px;margin:0 auto}}h1{{font-size:24px;font-weight:600;margin:0 0 12px}}
.firm{{color:#5b606b;font-size:14px;letter-spacing:.06em;text-transform:uppercase;margin:0 0 28px}}
a{{color:#2f4f85}}</style></head>
<body><main><p class="firm">Morgan and Morgan</p><h1>{html.escape(title)}</h1><p>{html.escape(message)}</p>{action}</main>
</body></html>""".encode()


BROKEN = ("This link isn't working right now", "Please try again in a few minutes. If it still doesn't open, your case "
          "team will send you a new one.")
SIGNED = ("Thank you, you're all signed", "An attorney will review everything and countersign. The agreement is only "
          "final once they have, and you'll get a copy of the signed documents.")
NOT_FINISHED = ("Your documents are saved", "You can come back to them any time with the link in your email, and "
                "sign whenever you're ready.")
DECLINED = ("You chose not to sign", "That's completely fine. If you have questions or change your mind, your case "
            "team is happy to help.")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        parts = [p for p in url.path.split("/") if p]
        if len(parts) not in (3, 4) or parts[0] != "sign" or (len(parts) == 4 and parts[3] != "done") \
                or not valid(parts[1], parts[2]):
            return self.reply(404, page("Page not found", "Check the link in your email."))
        envelope_id, sig = parts[1], parts[2]
        own_link = f"{public_url()}/sign/{envelope_id}/{sig}"

        if len(parts) == 3:
            session = esign.signing_url(envelope_id, return_url=f"{own_link}/done")
            if not session:
                return self.reply(502, page(*BROKEN))
            self.send_response(302)
            self.send_header("Location", session)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return None

        event = urllib.parse.parse_qs(url.query).get("event", [""])[0]
        if event == "signing_complete":
            # the event parameter can be typed by anyone holding the link, so DocuSign confirms it
            call_id = esign.client_signed(envelope_id)
            if call_id:
                signed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
                crm.update_documents(call_id, {"status": "client_signed", "signedAt": signed_at})
                logger.info("Client signed the documents (session: %s)", call_id)
                return self.reply(200, page(*SIGNED))
        if event == "decline":
            return self.reply(200, page(*DECLINED))
        return self.reply(200, page(*NOT_FINISHED, link=own_link, link_text="Continue to your documents"))

    def reply(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # same signature as BaseHTTPRequestHandler
        pass  # paths carry envelope IDs and link signatures: keep them out of the console


def start(port: int = PORT) -> ThreadingHTTPServer:
    """Serves on a daemon thread; main.py starts it next to the agent. ngrok forwards the public URL here."""
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, name="signing-server", daemon=True).start()
    logger.info("Signing page listening on http://127.0.0.1:%d (public: %s)", port, public_url() or "not set")
    return server
