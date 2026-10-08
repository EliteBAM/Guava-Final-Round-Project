"""
Signing-packet tests: the DocuSign envelope, the signing link's page, texting, and .env loading. Offline: DocuSign,
the CRM and Guava's SMS API are patched or stubbed.
"""

import base64
import os
import re
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import date
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_opening import main  # noqa: E402,F401  (shares the offline import setup)

import crm  # noqa: E402
import esign  # noqa: E402
import settings  # noqa: E402
import signing_server  # noqa: E402
import texting  # noqa: E402

ASSETS = Path(__file__).resolve().parents[2] / "Assets"
ANCHOR = re.compile(re.escape(chr(92)) + "[a-z]_[a-z]+" + re.escape(chr(92)))
ENVELOPE = "1b2c3d4e-0000-4000-8000-123456789abc"


def anchors_in(tabs: dict) -> set[str]:
    return {tab["anchorString"] for kind in tabs.values() for tab in kind}


class TestEnvelope(unittest.TestCase):
    def setUp(self):
        env = {"ATTORNEY_NAME": "Jordan Reyes", "ATTORNEY_EMAIL": "attorney@example.com"}
        with mock.patch.dict(os.environ, env):
            self.envelope = esign.envelope_definition(
                "call-7", "Ana Lopez", "ana@example.com", date(2026, 9, 30),
                [("Statement", b"%PDF-a"), ("Agreement", b"%PDF-b")],
                today=date(2026, 10, 8))
        self.client, self.attorney = self.envelope["recipients"]["signers"]

    def test_documents_keep_their_signing_order(self):
        docs = self.envelope["documents"]
        self.assertEqual([("1", "Statement"), ("2", "Agreement")], [(d["documentId"], d["name"]) for d in docs])
        self.assertEqual(b"%PDF-a", base64.b64decode(docs[0]["documentBase64"]))

    def test_client_signs_first_and_is_embedded(self):
        self.assertEqual(("1", "call-7", "Ana Lopez"),
                         (self.client["routingOrder"], self.client["clientUserId"], self.client["name"]))
        self.assertEqual(("2", "Jordan Reyes", "attorney@example.com"),
                         (self.attorney["routingOrder"], self.attorney["name"], self.attorney["email"]))
        self.assertNotIn("clientUserId", self.attorney)  # DocuSign emails the attorney

    def test_it_is_a_draft_addressed_to_the_client(self):
        # send_envelope sends it once our link is set as the start URL
        self.assertEqual("created", self.envelope["status"])
        self.assertEqual("ana@example.com", self.client["email"])

    def test_call_details_are_filled_in_and_locked(self):
        text = {tab["tabLabel"]: tab for tab in self.client["tabs"]["textTabs"]}
        self.assertEqual(("Ana Lopez", "true"), (text["client_name"]["value"], text["client_name"]["locked"]))
        self.assertEqual("September 30, 2026", text["incident_date"]["value"])
        self.assertEqual("October 08, 2026", text["prepared_date"]["value"])
        self.assertNotIn("locked", text["date_of_birth"])  # the client types it

    def test_every_template_anchor_has_a_field(self):
        # a typo on either side would leave a signature line with nothing on it
        in_templates = {a for page in ASSETS.glob("*.html") for a in ANCHOR.findall(page.read_text(encoding="utf-8"))}
        in_tabs = anchors_in(self.client["tabs"]) | anchors_in(self.attorney["tabs"])
        self.assertEqual(in_templates, in_tabs)

    def test_missing_settings_mean_no_envelope(self):
        with mock.patch.dict(os.environ, {"DOCUSIGN_INTEGRATION_KEY": ""}):
            self.assertIsNone(esign.create_envelope("call-7", "Ana", "ana@example.com", None, []))


class TestSendEnvelope(unittest.TestCase):
    SIGNER = {"recipientId": "1", "name": "Ana Lopez", "email": "ana@example.com", "clientUserId": "call-7"}

    def send(self, side_effect) -> tuple[bool, mock.MagicMock]:
        with mock.patch.object(esign, "_account", return_value=("token", "https://ds.test/accounts/1")),                 mock.patch.object(esign, "_call", side_effect=side_effect) as call:
            return esign.send_envelope(ENVELOPE, "https://signing.test/sign/x/y"), call

    def test_sets_our_page_as_the_start_url_then_sends(self):
        sent, call = self.send([{"signers": [self.SIGNER]}, {}, {}])
        self.assertTrue(sent)
        (_, recipients), (_, update), (_, status) = [c.args for c in call.call_args_list]
        self.assertTrue(recipients.endswith(f"/envelopes/{ENVELOPE}/recipients"))
        signer = call.call_args_list[1].kwargs["body"]["signers"][0]
        self.assertEqual({**self.SIGNER, "embeddedRecipientStartURL": "https://signing.test/sign/x/y"}, signer)
        self.assertEqual(("PUT", "PUT"), (call.call_args_list[1].args[0], call.call_args_list[2].args[0]))
        self.assertTrue(status.endswith(f"/envelopes/{ENVELOPE}"))
        self.assertEqual({"status": "sent"}, call.call_args_list[2].kwargs["body"])

    def test_a_failure_means_not_sent(self):
        sent, _ = self.send(urllib.error.URLError("down"))
        self.assertFalse(sent)

    def test_emails_are_normalized(self):
        for given, expected in (("ana@example.com", "ana@example.com"), (" Ana.Lopez @ Gmail.com ", "ana.lopez@gmail.com"),
                                ("none", None), ("ana at gmail", None), (None, None), ("ana@gmail", None)):
            self.assertEqual(expected, esign.normalize_email(given), given)


class TestTexting(unittest.TestCase):
    def test_numbers_are_normalized(self):
        for given, expected in (("+14075550123", "+14075550123"), ("(407) 555-0123", "+14075550123"),
                                ("1 407 555 0123", "+14075550123"), ("555-0123", None), ("none", None), (None, None)):
            self.assertEqual(expected, texting.normalize_us_number(given), given)
        self.assertEqual("0, 1, 2, 3", texting.spoken_last4("+14075550123"))

    def test_nothing_is_sent_unless_enabled(self):
        with mock.patch.dict(os.environ, {"SMS_ENABLED": ""}), mock.patch.object(texting.guava, "Client") as client:
            self.assertEqual("disabled", texting.send_documents_text("+1484", "+1407", "https://x"))
        client.assert_not_called()

    def test_enabled_sends_through_guava(self):
        with mock.patch.dict(os.environ, {"SMS_ENABLED": "1"}), mock.patch.object(texting.guava, "Client") as client:
            self.assertEqual("ok", texting.send_documents_text("+14843040566", "+14075550123", "https://x/sign"))
            client.return_value.send_sms.side_effect = RuntimeError("not registered")
            self.assertEqual("error", texting.send_documents_text("+14843040566", "+14075550123", "https://x"))
        kwargs = client.return_value.send_sms.call_args_list[0].kwargs
        self.assertEqual(("+14843040566", "+14075550123"), (kwargs["from_number"], kwargs["to_number"]))
        self.assertIn("https://x/sign", kwargs["message"])
        self.assertIn("Reply STOP", kwargs["message"])

    def test_a_refused_send_logs_guavas_reason_not_the_link(self):
        request = httpx.Request("POST", "https://guava.example/v1/send-sms")
        refused = httpx.Response(403, text='{"error": "number not enabled for SMS"}', request=request)
        error = httpx.HTTPStatusError("refused", request=request, response=refused)
        with mock.patch.dict(os.environ, {"SMS_ENABLED": "1"}), mock.patch.object(texting.guava, "Client") as client, \
                self.assertLogs("guava.intro_agent", "WARNING") as logs:
            client.return_value.send_sms.side_effect = error
            self.assertEqual("error", texting.send_documents_text("+14843040566", "+14075550123", "https://x/s/1"))
        self.assertIn("HTTP 403", logs.output[0])
        self.assertIn("number not enabled for SMS", logs.output[0])
        self.assertNotIn("https://x/s/1", logs.output[0])


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class TestSigningServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.env = mock.patch.dict(os.environ, {"SIGNING_SECRET": "test-secret",
                                               "SIGNING_PUBLIC_URL": "https://signing.test/"})
        cls.env.start()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), signing_server.Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        cls.opener = urllib.request.build_opener(NoRedirects)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.env.stop()

    def get(self, path: str) -> tuple[int, str, str]:
        try:
            with self.opener.open(self.base + path, timeout=5) as response:
                return response.status, response.headers.get("Location", ""), response.read().decode()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers.get("Location", ""), exc.read().decode()

    def path(self) -> str:
        return (signing_server.link_for(ENVELOPE) or "").removeprefix("https://signing.test")

    def test_a_bare_domain_gets_https(self):
        # DocuSign forwards the email's button to this link, so it has to be absolute
        with mock.patch.dict(os.environ, {"SIGNING_PUBLIC_URL": "name.ngrok-free.dev/"}):
            self.assertEqual("https://name.ngrok-free.dev", signing_server.public_url())

    def test_link_is_signed(self):
        self.assertEqual(f"https://signing.test/sign/{ENVELOPE}/{signing_server.signature(ENVELOPE)}",
                         signing_server.link_for(ENVELOPE))
        with mock.patch.dict(os.environ, {"SIGNING_SECRET": ""}):
            self.assertIsNone(signing_server.link_for(ENVELOPE))

    def test_tap_opens_a_fresh_docusign_session(self):
        with mock.patch.object(esign, "signing_url", return_value="https://docusign.test/session") as session:
            status, location, _ = self.get(self.path())
        self.assertEqual((302, "https://docusign.test/session"), (status, location))
        self.assertEqual(f"https://signing.test{self.path()}/done", session.call_args.kwargs["return_url"])

    def test_tampered_or_unknown_links_are_refused(self):
        sig = signing_server.signature(ENVELOPE)
        with mock.patch.object(esign, "signing_url") as session:
            for path in (f"/sign/{ENVELOPE}/{'0' * 32}", f"/sign/not-an-envelope/{sig}", "/", "/consent"):
                self.assertEqual(404, self.get(path)[0], path)
        session.assert_not_called()

    def test_docusign_failure_shows_a_friendly_page(self):
        with mock.patch.object(esign, "signing_url", return_value=None):
            status, _, body = self.get(self.path())
        self.assertEqual(502, status)
        self.assertIn("isn&#x27;t working right now", body)

    def test_signing_complete_is_confirmed_before_the_crm_is_told(self):
        with mock.patch.object(esign, "client_signed", return_value="call-7"), \
                mock.patch.object(crm, "update_documents", return_value="ok") as update:
            status, _, body = self.get(self.path() + "/done?event=signing_complete")
        self.assertEqual(200, status)
        self.assertIn("all signed", body)
        self.assertEqual(("call-7", "client_signed"), (update.call_args.args[0], update.call_args.args[1]["status"]))

        # a typed-in event that DocuSign doesn't confirm changes nothing
        with mock.patch.object(esign, "client_signed", return_value=None), \
                mock.patch.object(crm, "update_documents") as update:
            _, _, body = self.get(self.path() + "/done?event=signing_complete")
        update.assert_not_called()
        self.assertIn("Continue to your documents", body)


class TestSettings(unittest.TestCase):
    def test_env_file(self):
        content = ("﻿# DocuSign\nA_KEY=abc   # a comment\nexport B_KEY=\"quoted # kept\"\n\nC_KEY=x#y\n"
                   "EXISTING=from-file\n")
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"EXISTING": "from-env"}):
            path = Path(tmp) / ".env"
            path.write_text(content, encoding="utf-8")
            settings.load_env_file(path)
            values = [os.environ.pop(k) for k in ("A_KEY", "B_KEY", "C_KEY")] + [os.environ["EXISTING"]]
        self.assertEqual(["abc", "quoted # kept", "x#y", "from-env"], values)


if __name__ == "__main__":
    unittest.main()
