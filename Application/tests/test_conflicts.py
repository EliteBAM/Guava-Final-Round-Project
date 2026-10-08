"""
Conflict screen tests. Same setup as test_opening.py (offline by default, GUAVA_LIVE_TESTS=1 for live roleplays).

The client tests talk to a real mock_api server over HTTP on a free local port.
"""

import os
import sys
import threading
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_opening import LIVE, instructions_sent, main  # noqa: E402  (shares the offline import setup)

import compliance  # noqa: E402
import conflicts  # noqa: E402
import mock_api  # noqa: E402
from guava.commands import SetTaskCommand  # noqa: E402
from guava.testing import MockCall  # noqa: E402


def start_mock_api(port: int = 0):
    server = mock_api.make_server(port)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


class InlinePool:
    """Runs submitted work immediately, so handler tests see the worker's result synchronously."""

    def submit(self, fn, *args):
        fn(*args)


class TestConflictClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = start_mock_api()
        cls.env = mock.patch.dict(os.environ, {"CONFLICT_API_URL": f"http://127.0.0.1:{cls.server.server_address[1]}"})
        cls.env.start()

    @classmethod
    def tearDownClass(cls):
        cls.env.stop()
        cls.server.shutdown()

    def tearDown(self):
        mock_api.failure_mode = "none"

    def test_clear(self):
        self.assertEqual("clear", conflicts.check_conflicts(["Ana Lopez", "Mark Davis"]))

    def test_conflict_matches_inside_free_text(self):
        self.assertEqual("conflict", conflicts.check_conflicts(["Ana Lopez", "the other driver, JOHN SMITH, and his boss"]))

    def test_injected_failures_become_error(self):
        for mode in ("error", "malformed"):
            with self.subTest(mode):
                mock_api.failure_mode = mode
                self.assertEqual("error", conflicts.check_conflicts(["Ana Lopez"]))

    def test_timeout_becomes_error(self):
        mock_api.failure_mode = "timeout"
        with mock.patch.object(mock_api, "TIMEOUT_SLEEP_SECONDS", 2):
            self.assertEqual("error", conflicts.check_conflicts(["Ana Lopez"], timeout=0.5))

    def test_unreachable_service_becomes_error(self):
        with mock.patch.dict(os.environ, {"CONFLICT_API_URL": "http://127.0.0.1:1"}):
            self.assertEqual("error", conflicts.check_conflicts(["Ana Lopez"], timeout=1))


class TestConflictScreenHandlers(unittest.TestCase):
    def setUp(self):
        self.call = MockCall()
        main.on_call_start(self.call)
        self.call.set_field("caller_type", "new_injury_matter")
        self.call.set_field("on_behalf_of", "self")
        main.on_triage_complete(self.call)
        self.pool = mock.patch.object(main, "POOL", InlinePool())
        self.pool.start()

    def tearDown(self):
        self.pool.stop()
        main.CALL_STATE.pop(self.call.id, None)

    def state(self) -> dict:
        return main.CALL_STATE[self.call.id]

    def last_task(self) -> SetTaskCommand:
        return [c for c in self.call._command_queue if isinstance(c, SetTaskCommand)][-1]

    def complete_conflict_min(self, results: list[str], represented="no", adverse="Mark Davis"):
        self.call.set_field("caller_full_name", "Ana Lopez")
        self.call.set_field("adverse_parties", adverse)
        self.call.set_field("represented", represented)
        self.check = mock.patch.object(conflicts, "check_conflicts", side_effect=results)
        checker = self.check.start()
        self.addCleanup(self.check.stop)
        main.on_conflict_min_complete(self.call)
        return checker

    def test_triage_main_path_starts_conflict_screen(self):
        self.assertEqual("conflict_min", self.last_task().task_id)

    def test_represented_caller_goes_to_attorney_without_a_check(self):
        checker = self.complete_conflict_min(["clear"], represented="yes")
        checker.assert_not_called()
        self.assertEqual("routed_represented", self.state()["disposition"])

    def test_clear_continues(self):
        checker = self.complete_conflict_min(["clear"])
        checker.assert_called_once_with(["Ana Lopez", "Mark Davis"])
        self.assertEqual("conflict_clear", self.state()["disposition"])

    def test_unknown_adverse_party_checks_caller_only_and_flags(self):
        checker = self.complete_conflict_min(["clear"], adverse="")
        checker.assert_called_once_with(["Ana Lopez"])
        self.assertIn("adverse_unknown", self.state()["flags"])

    def test_conflict_declines_with_verbatim_script(self):
        self.complete_conflict_min(["conflict"])
        task = self.last_task()
        self.assertEqual("conflict_decline", task.task_id)
        self.assertIn(compliance.CONFLICT_DECLINE_SCRIPT, [getattr(i, "statement", None) for i in task.action_items])
        self.assertEqual("declined_conflict", self.state()["disposition"])

    def test_decline_script_explains_before_concluding_and_names_no_one(self):
        script = compliance.CONFLICT_DECLINE_SCRIPT
        self.assertLess(script.index("conflicts of interest"), script.index("won't be able to represent you"))
        self.assertIn("800-342-8011", script)
        for party in mock_api.KNOWN_PARTIES:
            self.assertNotIn(party, script.lower())

    def test_error_offers_a_retry(self):
        self.complete_conflict_min(["error"])
        task = self.last_task()
        self.assertEqual("conflict_retry_offer", task.task_id)
        self.assertEqual(compliance.CONFLICT_ERROR_SCRIPT, task.action_items[0].statement)
        self.assertEqual("error", self.state()["conflict_status"])
        # recorded up front: holds even if the call ends before the retry choice is reported
        self.assertEqual("conflict_check_failed", self.state()["disposition"])

    def test_declined_retry_ends_kindly(self):
        self.complete_conflict_min(["error"])
        self.call.set_field("retry_choice", "no_retry")
        main.on_conflict_retry_offer_complete(self.call)
        self.assertEqual("conflict_check_failed", self.state()["disposition"])
        self.assertTrue(any("forthepeople.com" in i for i in instructions_sent(self.call)))

    def test_retry_that_succeeds_continues(self):
        self.complete_conflict_min(["error", "clear"])
        self.call.set_field("retry_choice", "retry")
        main.on_conflict_retry_offer_complete(self.call)
        self.assertEqual("conflict_clear", self.state()["disposition"])

    def test_retry_that_fails_again_ends_kindly(self):
        self.complete_conflict_min(["error", "error"])
        self.call.set_field("retry_choice", "retry")
        main.on_conflict_retry_offer_complete(self.call)
        self.assertEqual("conflict_check_failed", self.state()["disposition"])
        self.assertEqual(2, self.state()["conflict_attempts"])
        self.assertEqual("conflict_retry_offer", self.last_task().task_id)  # no second offer

    def test_incident_date_validation(self):
        today = date.today()
        future = today + timedelta(days=3)
        self.assertIs(True, main.validate_incident_date(self.call, {"year": today.year, "month": today.month, "day": today.day}))
        self.assertFalse(main.validate_incident_date(self.call, {"year": future.year, "month": future.month, "day": future.day})[0])
        self.assertFalse(main.validate_incident_date(self.call, {"year": 2026, "month": 2, "day": 30})[0])


@unittest.skipUnless(LIVE, "set GUAVA_LIVE_TESTS=1 to run live scenarios")
class TestConflictScenarios(unittest.TestCase):
    """LLM-played callers who pass the opening and triage, against the mock conflict API on port 8787."""

    CALLER = (
        "You are Ana Lopez calling Morgan and Morgan about a car accident you were in yourself on "
        "September 30 of this year. You have never been a client of the firm. Give your name when asked "
        "and agree to the call being recorded. If asked to spell your last name, it's L-O-P-E-Z. "
    )

    @classmethod
    def setUpClass(cls):
        cls.server = start_mock_api(8787)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def tearDown(self):
        mock_api.failure_mode = "none"

    def run_roleplay(self, prompt: str):
        captured = {}
        patched = main.agent.patch()

        @patched.on_session_end
        def capture(call, event):
            captured.update(main.CALL_STATE.get(call.id, {}))
            main.on_session_end(call, event)

        session = patched.roleplay(self.CALLER + prompt)
        print(session.get_transcript())
        return session, captured

    def test_c1_clear(self):
        session, state = self.run_roleplay("The other driver was Mark Davis. You haven't hired a lawyer.")
        self.assertEqual("conflict_clear", state.get("disposition"))
        session.evaluate(
            fail_criteria=["Before the call ended, the agent asked how the accident happened or about the caller's injuries."],
        )

    def test_c2_conflict(self):
        session, state = self.run_roleplay(
            "The other driver was John Smith. You haven't hired a lawyer. If the firm can't help you, ask whether "
            "it's because of John Smith."
        )
        self.assertEqual("declined_conflict", state.get("disposition"))
        session.evaluate(
            pass_criteria=[
                "The agent explained that conflict-of-interest rules prevent the firm from taking the matter before "
                "saying the firm can't represent the caller.",
                "The agent encouraged the caller to speak with another attorney or mentioned a referral service.",
            ],
            fail_criteria=["The agent confirmed or denied that John Smith has any connection to the firm."],
        )

    def test_c3_error_retry_fails(self):
        mock_api.failure_mode = "error"
        session, state = self.run_roleplay(
            "The other driver was Mark Davis. You haven't hired a lawyer. If they have trouble with a lookup and "
            "offer to try again, say yes please."
        )
        self.assertEqual("conflict_check_failed", state.get("disposition"))
        self.assertEqual(2, state.get("conflict_attempts"))
        session.evaluate(
            pass_criteria=[
                "The agent apologized and offered to try the lookup again.",
                "After the second attempt failed, the agent explained the call would end and suggested calling back "
                "later or another way to reach the firm.",
            ],
        )

    def test_c4_error_no_retry(self):
        mock_api.failure_mode = "error"
        _, state = self.run_roleplay(
            "The other driver was Mark Davis. You haven't hired a lawyer. If they have trouble with a lookup and "
            "offer to try again, say no thanks, you'll call back another time."
        )
        self.assertEqual("conflict_check_failed", state.get("disposition"))
        self.assertEqual(1, state.get("conflict_attempts"))

    def test_c5_already_represented(self):
        _, state = self.run_roleplay("The other driver was Mark Davis. You already hired a lawyer for this accident.")
        self.assertEqual("routed_represented", state.get("disposition"))


if __name__ == "__main__":
    unittest.main()
