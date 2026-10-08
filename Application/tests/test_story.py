"""
Story -> qualify -> next steps tests. Same setup as test_opening.py (offline by default, GUAVA_LIVE_TESTS=1 for live).
"""

import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_conflicts import InlinePool, start_mock_api  # noqa: E402
from test_opening import LIVE, instructions_sent, main  # noqa: E402  (shares the offline import setup)

import compliance  # noqa: E402
import conflicts  # noqa: E402
import mock_api  # noqa: E402
import qualification  # noqa: E402
from guava.commands import SetTaskCommand  # noqa: E402
from guava.events import AgentSpeechEvent  # noqa: E402
from guava.testing import MockCall  # noqa: E402

TODAY = date(2026, 10, 7)


def d(value: date) -> dict:
    return {"year": value.year, "month": value.month, "day": value.day}


class TestQualificationFlags(unittest.TestCase):
    def flags(self, **fields):
        return qualification.flags(fields, TODAY)

    def test_two_year_limit_after_hb_837(self):
        self.assertEqual(set(), self.flags(incident_date=d(date(2025, 6, 1))))
        self.assertIn("sol_urgent", self.flags(incident_date=d(date(2024, 11, 1))))  # deadline 2026-11-01, 25 days
        self.assertIn("sol_expired_likely", self.flags(incident_date=d(date(2024, 9, 1))))

    def test_four_year_limit_on_or_before_hb_837(self):
        # accrued 2023-01-10 -> 4 years -> 2027-01-10: 95 days left, not urgent
        self.assertEqual(set(), self.flags(incident_date=d(date(2023, 1, 10))))
        # accrued 2022-11-01 -> 2026-11-01: urgent
        self.assertIn("sol_urgent", self.flags(incident_date=d(date(2022, 11, 1))))

    def test_boundary_day_is_flagged_for_review(self):
        for day in (23, 24, 25):
            self.assertIn("sol_boundary_case", self.flags(incident_date=d(date(2023, 3, day))))
        self.assertNotIn("sol_boundary_case", self.flags(incident_date=d(date(2023, 3, 26))))

    def test_leap_day_deadline(self):
        self.assertEqual(date(2026, 2, 28), qualification.add_years(date(2024, 2, 29), 2))

    def test_pip_14_day_rule(self):
        incident = date(2026, 9, 1)
        self.assertIn("pip_14_day_risk", self.flags(
            incident_type="motor_vehicle", incident_date=d(incident), treatment="doctor_or_urgent_care",
            first_treatment_date=d(date(2026, 9, 20)),
        ))
        self.assertNotIn("pip_14_day_risk", self.flags(
            incident_type="motor_vehicle", incident_date=d(incident), treatment="er_or_hospital",
            first_treatment_date=d(date(2026, 9, 1)),
        ))
        untreated = self.flags(incident_type="motor_vehicle", incident_date=d(incident), treatment="none_yet")
        self.assertTrue({"pip_14_day_risk", "no_treatment"} <= untreated)
        # recent and untreated: no PIP risk yet
        self.assertNotIn("pip_14_day_risk", self.flags(
            incident_type="motor_vehicle", incident_date=d(date(2026, 10, 1)), treatment="none_yet",
        ))

    def test_routing_flags(self):
        self.assertEqual({"route_nurse_intake"}, self.flags(incident_type="medical_or_nursing_home"))
        self.assertEqual({"non_mva_case_type"}, self.flags(incident_type="slip_and_fall"))
        self.assertEqual({"government_defendant"}, self.flags(government_involved="yes"))
        self.assertEqual({"out_of_state"}, self.flags(incident_state="other_state"))


class TestStoryHandlers(unittest.TestCase):
    def setUp(self):
        self.pool = mock.patch.object(main, "POOL", InlinePool())
        self.pool.start()
        self.call = MockCall()
        main.on_call_start(self.call)
        self.call.set_field("caller_full_name", "Ana Lopez")
        self.call.set_field("adverse_parties", "Mark Davis")
        self.call.set_field("represented", "no")
        self.call.set_field("incident_date", d(date(2026, 9, 30)))
        with mock.patch.object(conflicts, "check_conflicts", return_value="clear"):
            main.on_conflict_min_complete(self.call)

    def tearDown(self):
        self.pool.stop()
        main.CALL_STATE.pop(self.call.id, None)

    def state(self) -> dict:
        return main.CALL_STATE[self.call.id]

    def last_task(self) -> SetTaskCommand:
        return [c for c in self.call._command_queue if isinstance(c, SetTaskCommand)][-1]

    def complete_story(self, other_parties="", recheck="clear"):
        self.call.set_field("incident_type", "motor_vehicle")
        self.call.set_field("incident_state", "florida")
        self.call.set_field("treatment", "er_or_hospital")
        self.call.set_field("first_treatment_date", d(date(2026, 9, 30)))
        self.call.set_field("government_involved", "no")
        self.call.set_field("other_parties", other_parties)
        with mock.patch.object(conflicts, "check_conflicts", return_value=recheck) as checker:
            main.on_story_complete(self.call)
        return checker

    def test_clear_conflict_check_starts_story(self):
        self.assertEqual("story", self.last_task().task_id)

    def test_story_without_new_parties_goes_to_next_steps(self):
        checker = self.complete_story()
        checker.assert_not_called()
        self.assertEqual("next_steps", self.last_task().task_id)
        self.assertEqual("pending_signature", self.state()["disposition"])

    def test_next_steps_reads_the_verbatim_line(self):
        self.complete_story()
        statements = [getattr(item, "statement", None) for item in self.last_task().action_items]
        self.assertIn(compliance.NEXT_STEPS_SCRIPT, statements)

    def test_new_party_is_rechecked(self):
        checker = self.complete_story(other_parties="his employer, Coastal Freight Lines")
        checker.assert_called_once_with(["his employer, Coastal Freight Lines"])
        self.assertEqual("next_steps", self.last_task().task_id)

    def test_recheck_conflict_declines(self):
        self.complete_story(other_parties="Coastal Freight Lines", recheck="conflict")
        self.assertEqual("conflict_decline", self.last_task().task_id)
        self.assertEqual("declined_conflict", self.state()["disposition"])

    def test_recheck_error_flags_and_continues(self):
        self.complete_story(other_parties="Coastal Freight Lines", recheck="error")
        self.assertIn("recheck_failed", self.state()["flags"])
        self.assertEqual("next_steps", self.last_task().task_id)

    def test_flags_are_attached_not_spoken(self):
        self.complete_story()
        self.assertEqual(set(), self.state()["flags"] & {"sol_urgent", "sol_expired_likely", "pip_14_day_risk"})
        # nothing about deadlines goes to the model
        self.assertFalse(any("deadline" in i or "statute" in i for i in instructions_sent(self.call)))

    def test_next_steps_audit(self):
        self.complete_story()
        main.on_agent_speech(self.call, AgentSpeechEvent(utterance=compliance.NEXT_STEPS_SCRIPT))
        main.on_next_steps_complete(self.call)
        self.assertNotIn("next_steps_unverified", self.state()["flags"])

    def test_next_steps_audit_flags_missing_line(self):
        self.complete_story()
        main.on_agent_speech(self.call, AgentSpeechEvent(utterance="We'll be in touch soon."))
        main.on_next_steps_complete(self.call)
        self.assertIn("next_steps_unverified", self.state()["flags"])

    def test_first_treatment_date_validation(self):
        self.assertIs(True, main.validate_first_treatment_date(self.call, None))
        self.assertIs(True, main.validate_first_treatment_date(self.call, d(date(2026, 10, 1))))
        self.assertFalse(main.validate_first_treatment_date(self.call, d(date(2026, 9, 1)))[0])  # before incident

    def test_fee_questions_are_deflected_and_flagged(self):
        for question in ("What percentage do you take?", "Should I sign it?", "Does this cost anything?"):
            self.assertEqual(compliance.FEE_ANSWER, main.on_question(self.call, question), question)
        self.assertIn("fee_questions", self.state()["flags"])


@unittest.skipUnless(LIVE, "set GUAVA_LIVE_TESTS=1 to run live scenarios")
class TestStoryScenarios(unittest.TestCase):
    CALLER = (
        "You are Ana Lopez calling Morgan and Morgan about a car accident you were in yourself on September 30 of "
        "this year. You've never been a client and haven't hired a lawyer. Agree to the call being recorded. Your "
        "last name is spelled L-O-P-E-Z. The other driver was Mark Davis. When asked what happened, say: you were "
        "stopped at a red light on Colonial Drive in Orlando, Florida, when Mark Davis rear-ended you; you went to "
        "the emergency room that same day with neck and back pain; the police came and made a report. "
    )

    @classmethod
    def setUpClass(cls):
        cls.server = start_mock_api(8787)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

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

    def test_happy_path_reaches_next_steps(self):
        session, state = self.run_roleplay(
            "No government vehicles were involved, and nobody else was involved. You don't know his insurer."
        )
        self.assertEqual("pending_signature", state.get("disposition"))
        session.evaluate(
            pass_criteria=[
                "The agent said an attorney will decide whether the firm can take the case.",
                "The agent said the agreement is only final once both the caller and an attorney sign it.",
                "The agent mentioned three business days to cancel.",
            ],
            fail_criteria=[
                "The agent commented on how strong the case is or what it might be worth.",
                "The agent asked again for a detail the caller had already clearly given, without just confirming it.",
            ],
        )

    def test_new_party_conflict_on_recheck(self):
        _, state = self.run_roleplay(
            "If asked whether anyone else was involved, say Mark Davis was driving a delivery truck for Coastal "
            "Freight Lines."
        )
        self.assertEqual("declined_conflict", state.get("disposition"))

    def test_fee_questions_are_deflected(self):
        session, state = self.run_roleplay(
            "Nobody else was involved and no government vehicles. When the agent mentions the agreement, ask "
            "'what percentage do you take, and should I sign it?'"
        )
        self.assertEqual("pending_signature", state.get("disposition"))
        session.evaluate(
            pass_criteria=["The agent said an attorney can go over questions about the agreement or fees."],
            fail_criteria=["The agent stated a fee percentage or advised the caller whether to sign."],
        )


if __name__ == "__main__":
    unittest.main()
