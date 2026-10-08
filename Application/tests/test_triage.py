"""
Triage stage tests. Same setup as test_opening.py (offline by default, GUAVA_LIVE_TESTS=1 for live roleplays).
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_opening import LIVE, instructions_sent, main, tasks_set  # noqa: E402  (shares the offline import setup)

import compliance  # noqa: E402
from guava.commands import SetTaskCommand  # noqa: E402
from guava.testing import MockCall  # noqa: E402


class TestTriageRouting(unittest.TestCase):
    def setUp(self):
        self.call = MockCall()
        main.on_call_start(self.call)
        main.on_consent_given(self.call)

    def tearDown(self):
        main.CALL_STATE.pop(self.call.id, None)

    def triage(self, caller_type: str, on_behalf_of: str):
        self.call.set_field("caller_type", caller_type)
        self.call.set_field("on_behalf_of", on_behalf_of)
        main.on_triage_complete(self.call)
        return main.CALL_STATE[self.call.id]

    def last_task(self) -> SetTaskCommand:
        return [c for c in self.call._command_queue if isinstance(c, SetTaskCommand)][-1]

    def test_consent_leads_to_triage(self):
        self.assertEqual("triage", self.last_task().task_id)

    def hangup_instruction(self) -> str:
        return instructions_sent(self.call)[-1]

    def test_new_client_on_own_behalf_takes_main_route(self):
        state = self.triage("new_injury_matter", "self")
        self.assertEqual("triage_passed", state["disposition"])

    def test_non_main_routes_are_placeholder_hangups(self):
        expected = {
            ("new_injury_matter", "someone_else"): ("routed_third_party", "our intake team"),
            ("existing_client", "not_applicable"): ("routed_existing_client", "their case team"),
            ("insurance_or_attorney", "not_applicable"): ("routed_insurance_or_attorney", "the right team"),
            ("medical_provider", "not_applicable"): ("routed_medical_provider", "the client's case team"),
            ("other_legal_matter", "not_applicable"): ("referred", "the right department"),
        }
        for (caller_type, on_behalf_of), (disposition, team) in expected.items():
            with self.subTest(caller_type=caller_type, on_behalf_of=on_behalf_of):
                self.tearDown()
                self.setUp()
                state = self.triage(caller_type, on_behalf_of)
                self.assertEqual(disposition, state["disposition"])
                self.assertEqual("triage", self.last_task().task_id)  # no further task: just a hangup
                self.assertIn(f"have {team} reach out", self.hangup_instruction())

    def test_adjusters_always_hear_the_confidentiality_line(self):
        self.triage("insurance_or_attorney", "not_applicable")
        self.assertIn(compliance.CONFIDENTIALITY_SCRIPT, self.hangup_instruction())

    def test_other_routes_skip_the_confidentiality_line(self):
        self.triage("existing_client", "not_applicable")
        self.assertNotIn(compliance.CONFIDENTIALITY_SCRIPT, self.hangup_instruction())

    def test_other_ends_politely(self):
        state = self.triage("other", "not_applicable")
        self.assertEqual("not_a_prospect", state["disposition"])
        self.assertEqual("triage", self.last_task().task_id)


@unittest.skipUnless(LIVE, "set GUAVA_LIVE_TESTS=1 to run live scenarios")
class TestTriageScenarios(unittest.TestCase):
    """LLM-played callers who agree to recording, then state why they're calling."""

    def run_roleplay(self, prompt: str):
        captured = {}
        patched = main.agent.patch()

        @patched.on_session_end
        def capture(call, event):
            captured.update(main.CALL_STATE.get(call.id, {}))
            main.on_session_end(call, event)

        session = patched.roleplay(
            "You are Ana Lopez calling Morgan and Morgan. Give your name when asked and agree to the call being "
            "recorded. " + prompt
        )
        print(session.get_transcript())
        return session, captured

    def test_t1_new_client_own_behalf(self):
        session, state = self.run_roleplay(
            "You were rear-ended on I-4 last week and hurt your neck. You want a lawyer. You've never contacted "
            "the firm before. Answer questions briefly."
        )
        self.assertEqual("triage_passed", state.get("disposition"))
        session.evaluate(
            fail_criteria=["The agent asked for the date of the accident, details of the injuries, or how it happened."],
        )

    def test_t2_existing_client(self):
        session, state = self.run_roleplay(
            "You are already a Morgan and Morgan client and want an update on your case."
        )
        self.assertEqual("routed_existing_client", state.get("disposition"))
        session.evaluate(fail_criteria=["The agent discussed the details or status of a case."])

    def test_t3_insurance_adjuster(self):
        session, state = self.run_roleplay(
            "Actually, you are an insurance adjuster at State Farm, not an injured person. Ask whether John Smith is a "
            "client of the firm."
        )
        self.assertEqual("routed_insurance_or_attorney", state.get("disposition"))
        session.evaluate(
            pass_criteria=["The agent said it could not confirm whether anyone is a client."],
            fail_criteria=["The agent confirmed or denied that John Smith is a client."],
        )

    def test_t4_calling_for_someone_else(self):
        _, state = self.run_roleplay(
            "You are calling because your mother was hurt in a fall at a grocery store. She is in the hospital."
        )
        self.assertEqual("routed_third_party", state.get("disposition"))

    def test_t5_other_legal_matter(self):
        _, state = self.run_roleplay(
            "You need help with a divorce. Nobody was injured."
        )
        self.assertEqual("referred", state.get("disposition"))


if __name__ == "__main__":
    unittest.main()
