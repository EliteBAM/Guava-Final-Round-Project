"""
Story -> qualify -> next steps tests. Same setup as test_opening.py (offline by default, GUAVA_LIVE_TESTS=1 for live).
"""

import json
import sys
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_conflicts import InlinePool, start_mock_api  # noqa: E402
from test_opening import LIVE, instructions_sent, main  # noqa: E402  (shares the offline import setup)

import compliance  # noqa: E402
import conflicts  # noqa: E402
import crm  # noqa: E402
import esign  # noqa: E402
import intake  # noqa: E402
import mock_api  # noqa: E402
import qualification  # noqa: E402
import signing_server  # noqa: E402
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

    def complete_story(self, other_parties="", recheck="clear", incident_type="motor_vehicle", **details):
        self.call.set_field("incident_type", incident_type)
        self.call.set_field("incident_state", "florida")
        self.call.set_field("treatment", "er_or_hospital")
        self.call.set_field("first_treatment_date", d(date(2026, 9, 30)))
        self.call.set_field("government_involved", "no")
        self.call.set_field("other_parties", other_parties)
        with mock.patch.object(conflicts, "check_conflicts", return_value=recheck) as checker:
            main.on_story_complete(self.call)
            if incident_type in intake.MODULES:
                for key, value in {"vehicle_role": "driver", "other_vehicle": "personal", "on_the_job": "no",
                                   **details}.items():
                    self.call.set_field(key, value)
                main.on_details_complete(self.call)
        return checker

    def test_clear_conflict_check_starts_story(self):
        self.assertEqual("story", self.last_task().task_id)

    def test_story_without_new_parties_goes_to_next_steps(self):
        checker = self.complete_story()
        checker.assert_not_called()
        self.assertEqual("next_steps", self.last_task().task_id)
        self.assertEqual("pending_signature", self.state()["disposition"])

    def test_nobody_answer_is_not_rechecked(self):
        # live: the model wrote "none" into other_parties, which re-checked the word "none" as a party name
        checker = self.complete_story(other_parties="none")
        checker.assert_not_called()
        self.assertEqual("next_steps", self.last_task().task_id)

    def test_closing_tasks_read_the_verbatim_line(self):
        self.complete_story()
        main.start_documents_sent(self.call, "ana@example.com")
        main.start_documents_follow_up(self.call)
        for task in [c for c in self.call._command_queue if isinstance(c, SetTaskCommand)][-2:]:
            statements = [getattr(item, "statement", None) for item in task.action_items]
            self.assertIn(compliance.NEXT_STEPS_SCRIPT, statements, task.task_id)

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
        main.start_documents_follow_up(self.call)
        main.on_agent_speech(self.call, AgentSpeechEvent(utterance=compliance.NEXT_STEPS_SCRIPT))
        main.on_closing_complete(self.call)
        self.assertNotIn("next_steps_unverified", self.state()["flags"])

    def test_next_steps_audit_flags_missing_line(self):
        self.complete_story()
        main.start_documents_sent(self.call, "ana@example.com")
        main.on_agent_speech(self.call, AgentSpeechEvent(utterance="We'll be in touch soon."))
        main.on_closing_complete(self.call)
        self.assertIn("next_steps_unverified", self.state()["flags"])

    def test_first_treatment_date_validation(self):
        self.assertIs(True, main.validate_first_treatment_date(self.call, None))
        self.assertIs(True, main.validate_first_treatment_date(self.call, d(date(2026, 10, 1))))
        self.assertFalse(main.validate_first_treatment_date(self.call, d(date(2026, 9, 1)))[0])  # before incident

    def test_story_routes_to_case_type_module(self):
        for incident_type, (task_id, _) in intake.MODULES.items():
            self.call.set_field("incident_type", incident_type)
            main.on_story_complete(self.call)
            self.assertEqual(task_id, self.last_task().task_id)

    def test_other_case_type_skips_the_module(self):
        self.complete_story(incident_type="other")
        self.assertNotIn("details_mva", [t.task_id for t in self.call._command_queue if isinstance(t, SetTaskCommand)])
        self.assertEqual("next_steps", self.last_task().task_id)
        self.assertIn("non_mva_case_type", self.state()["flags"])

    def test_details_flags_reach_the_record_state(self):
        self.complete_story(other_vehicle="commercial_or_work", on_the_job="yes", seat_belt="no")
        self.assertTrue({"commercial_vehicle", "on_the_job", "no_seat_belt"} <= self.state()["flags"])

    def test_story_task_is_built_from_the_schema(self):
        main.start_story(self.call)
        keys = [item.key for item in self.last_task().action_items if getattr(item, "item_type", "") == "field"]
        self.assertEqual([intake.NARRATIVE.key] + [s.key for s in intake.CORE], keys)

    def write_record(self) -> tuple[dict, mock.MagicMock]:
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(main, "RECORDS_DIR", Path(tmp)), \
                mock.patch.object(crm, "upsert_pnc", return_value="ok") as upsert:
            main.write_intake_record(self.call, self.state())
            record = json.loads((Path(tmp) / f"{self.call.id}.json").read_text(encoding="utf-8"))
        return record, upsert

    def test_session_end_writes_the_record(self):
        self.complete_story()
        record, _ = self.write_record()
        self.assertEqual("pending_signature", record["disposition"])
        self.assertEqual("2026-09-30", record["incident"]["date"])
        self.assertEqual("Mark Davis", record["parties"]["adverse"])
        self.assertEqual("clear", record["conflicts"]["status"])

    def test_session_end_sends_the_record_to_the_crm(self):
        self.call.set_field("caller_type", "new_injury_matter")
        self.call.set_field("narrative", "Rear-ended at a red light.")
        self.complete_story()
        record, upsert = self.write_record()
        upsert.assert_called_once_with(self.call.id, "Ana Lopez", "Rear-ended at a red light.", record)

    def test_routed_callers_are_not_sent_to_the_crm(self):
        self.call.set_field("caller_type", "insurance_or_attorney")
        _, upsert = self.write_record()
        upsert.assert_not_called()

    # ---- emailing the signing packet

    TEMPLATES = [("Statement of Client’s Rights", b"%PDF-1"), ("Contingency Fee Agreement", b"%PDF-2"),
                 ("HIPAA Authorization", b"%PDF-3")]

    def send(self, email="Ana@Example.com", templates=TEMPLATES, envelope="env-1",
             link="https://signing.test/sign/env-1/sig", sent=True) -> dict:
        """Completes next_steps with every outside service patched; returns the mocks."""
        self.complete_story()
        self.call.set_field("documents_email", email)
        with mock.patch.object(crm, "upsert_pnc", return_value="ok") as upsert,                 mock.patch.object(crm, "fetch_templates", return_value=templates) as fetch,                 mock.patch.object(crm, "update_documents", return_value="ok") as update,                 mock.patch.object(esign, "create_envelope", return_value=envelope) as create,                 mock.patch.object(signing_server, "link_for", return_value=link),                 mock.patch.object(esign, "send_envelope", return_value=sent) as send:
            main.on_next_steps_complete(self.call)
        return {"upsert": upsert, "fetch": fetch, "update": update, "create": create, "send": send}

    def field_keys(self) -> list[str]:
        return [item.key for item in self.last_task().action_items if getattr(item, "item_type", "") == "field"]

    def test_next_steps_asks_for_an_email(self):
        self.complete_story()
        self.assertEqual(["documents_email"], self.field_keys())

    def test_an_email_sends_the_signing_packet(self):
        mocks = self.send()
        self.assertEqual("documents_sent", self.last_task().task_id)
        mocks["upsert"].assert_called_once()  # the PNC exists before its documents status is set
        mocks["fetch"].assert_called_once_with(main.SIGNING_PACKET)
        mocks["create"].assert_called_once_with(self.call.id, "Ana Lopez", "ana@example.com", date(2026, 9, 30),
                                                self.TEMPLATES)
        mocks["send"].assert_called_once_with("env-1", "https://signing.test/sign/env-1/sig")
        documents = self.state()["documents"]
        self.assertEqual(("sent", "env-1", "email", "ana@example.com"),
                         (documents["status"], documents["envelopeId"], documents["sentVia"], documents["sentTo"]))
        mocks["update"].assert_called_once_with(self.call.id, documents)
        self.assertNotIn("documents_not_sent", self.state()["flags"])

    def test_no_usable_email_means_the_team_sends_them(self):
        for email in ("none", "ana at gmail", None):
            self.state()["flags"].discard("documents_not_sent")
            mocks = self.send(email=email)
            mocks["create"].assert_not_called()
            mocks["send"].assert_not_called()
            self.assertEqual("documents_follow_up", self.last_task().task_id, email)
            self.assertIn("documents_not_sent", self.state()["flags"], email)

    def test_any_failed_step_means_the_team_sends_them(self):
        for failure in ({"templates": None}, {"envelope": None}, {"link": None}, {"sent": False}):
            self.state()["flags"].discard("documents_not_sent")
            self.send(**failure)
            self.assertEqual("documents_follow_up", self.last_task().task_id, failure)
            self.assertIn("documents_not_sent", self.state()["flags"], failure)
            self.assertNotIn("documents", self.state(), failure)

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

    def run_roleplay(self, prompt: str, caller: str = CALLER):
        captured = {}
        patched = main.agent.patch()

        @patched.on_session_end
        def capture(call, event):
            captured.update(main.CALL_STATE.get(call.id, {}))
            main.on_session_end(call, event)

        session = patched.roleplay(caller + prompt)
        print(session.get_transcript())
        return session, captured

    def test_happy_path_reaches_next_steps(self):
        session, state = self.run_roleplay(
            "No government vehicles were involved, and nobody else was involved. You were driving your own car "
            "with your seat belt on, and Mark was in his personal car. You weren't working. You don't know his "
            "insurer; yours is GEICO."
        )
        self.assertEqual("pending_signature", state.get("disposition"))
        session.evaluate(
            pass_criteria=[
                "The agent asked whether the caller was wearing a seat belt without commenting on what it means.",
                "Before moving on to next steps, the agent briefly recapped what happened, the injuries and the "
                "treatment, and asked if anything needed correcting.",
                "The agent said an attorney will decide whether the firm can take the case.",
                "The agent said the agreement is only final once both the caller and an attorney sign it.",
                "The agent mentioned three business days to cancel.",
            ],
            fail_criteria=[
                "The agent commented on how strong the case is, who was at fault, or what it might be worth.",
                "The agent asked again for a detail the caller had already clearly given, without just confirming it.",
                "The agent asked for a Social Security number, a policy number, or medical bill amounts.",
            ],
        )

    def test_new_party_conflict_on_recheck(self):
        _, state = self.run_roleplay(
            "If asked whether anyone else was involved, say Mark Davis was driving a delivery truck for Coastal "
            "Freight Lines."
        )
        self.assertEqual("declined_conflict", state.get("disposition"))

    def test_commercial_vehicle_on_the_job(self):
        _, state = self.run_roleplay(
            "You were driving to a customer's house for your job as a plumber. If asked about the other vehicle or "
            "anyone else involved, say Mark Davis was driving a work van for Sunrise Pool Services. No government "
            "vehicles."
        )
        self.assertEqual("pending_signature", state.get("disposition"))
        self.assertTrue({"commercial_vehicle", "on_the_job"} <= state.get("flags", set()))
        self.assertEqual("clear", state.get("recheck_status"))

    def test_unsure_caller_is_not_pressed(self):
        session, state = self.run_roleplay(
            "You're still shaken and fuzzy on details. You don't know whether there were witnesses, whether anyone "
            "took photos, what insurance either of you has, or whether you have uninsured motorist coverage; say "
            "'I'm not sure' to each. No government vehicles, nobody else involved, you weren't working."
        )
        self.assertEqual("pending_signature", state.get("disposition"))
        session.evaluate(
            pass_criteria=["The agent accepted 'I'm not sure' answers and moved on."],
            fail_criteria=["The agent asked the same question again after the caller said they weren't sure."],
        )

    def test_slip_and_fall_stub(self):
        _, state = self.run_roleplay(
            "When asked what happened, say: on September 30 of this year you slipped on spilled water in the "
            "produce aisle of a Publix in Orlando, Florida; there was no warning sign; you hurt your wrist and went "
            "to urgent care that day; you told the store manager, who wrote an incident report. No police, no "
            "government property, nobody else involved.",
            caller=(
                "You are Ana Lopez calling Morgan and Morgan about a fall you had yourself. You've never been a client "
                "and haven't hired a lawyer. Agree to the call being recorded. Your last name is spelled L-O-P-E-Z. "
                "The other party is the Publix store. "
            ),
        )
        self.assertEqual("pending_signature", state.get("disposition"))
        self.assertIn("non_mva_case_type", state.get("flags", set()))

    def test_medical_stub_routes_to_nurse_intake(self):
        _, state = self.run_roleplay(
            "When asked what happened, say: you had knee surgery on August 20 of this year at Orlando General "
            "with Dr. Alan Reyes, and in early September learned an infection had been missed; you needed a second "
            "surgery. You're still treating. No police, no government hospital, nobody else involved. If asked "
            "for an exact date you don't know, say you're not sure.",
            caller=(
                "You are Ana Lopez calling Morgan and Morgan about a medical problem that happened to you. You've "
                "never been a client and haven't hired a lawyer. Agree to the call being recorded. Your last name is "
                "spelled L-O-P-E-Z. The other party is Dr. Alan Reyes. "
            ),
        )
        self.assertEqual("pending_signature", state.get("disposition"))
        self.assertIn("route_nurse_intake", state.get("flags", set()))

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
