"""
Intake schema and record tests. Pure: no guava import except through the main.guava_field mapping test.
"""

import sys
import unittest
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_opening import main  # noqa: E402  (shares the offline import setup)

import intake  # noqa: E402
import qualification  # noqa: E402


class TestSchema(unittest.TestCase):
    def test_keys_are_unique(self):
        keys = [spec.key for spec in intake.ALL_SPECS] + list(intake.HEADER_KEYS)
        self.assertEqual(len(keys), len(set(keys)))

    def test_specs_are_well_formed(self):
        for spec in intake.ALL_SPECS:
            # critical or important only: a "never ask" tier can't resolve in Guava and stalled a task live
            self.assertIn(spec.tier, main.TIER_GUIDANCE, spec.key)
            self.assertIn(spec.section, ("incident", "liability", "injuries", "coverage", "parties"), spec.key)
            self.assertEqual(spec.kind == "multiple_choice", bool(spec.choices), spec.key)

    def test_each_module_lists_critical_fields_first(self):
        order = [intake.CRITICAL, intake.IMPORTANT]
        for specs in (intake.CORE, *(module for _, module in intake.MODULES.values())):
            ranks = [order.index(spec.tier) for spec in specs]
            self.assertEqual(sorted(ranks), ranks)

    def test_specs_for_picks_the_module(self):
        keys = {spec.key for spec in intake.specs_for("motor_vehicle")}
        self.assertTrue({"narrative", "injuries", "seat_belt"} <= keys)
        self.assertNotIn("hazard", keys)
        self.assertNotIn("seat_belt", {spec.key for spec in intake.specs_for("other")})


class TestGuavaFieldMapping(unittest.TestCase):
    def test_tiers_map_to_required_and_guidance(self):
        by_key = {spec.key: spec for spec in intake.ALL_SPECS}
        critical = main.guava_field(by_key["injuries"])
        optional_critical = main.guava_field(by_key["first_treatment_date"])
        important = main.guava_field(by_key["seat_belt"])

        self.assertTrue(critical.required)
        self.assertFalse(optional_critical.required)
        self.assertFalse(important.required)
        self.assertIn("Ask once", important.description)
        self.assertEqual(["yes", "no", "not_sure", "not_applicable"], important.choices)

    def test_every_field_has_a_dont_know_answer(self):
        # a field the model can't fill stalls the task (live: other_insurer, discovery_date)
        for spec in intake.ALL_SPECS:
            if spec.key != "narrative":
                description = main.guava_field(spec).description
                answerable = spec.kind == "multiple_choice" and "not_sure" not in spec.choices
                self.assertTrue(answerable or "don't know" in description or "no idea" in description, spec.key)


class TestRecord(unittest.TestCase):
    FIELDS = {
        "caller_name": "Ana", "caller_full_name": "Ana Lopez", "recording_consent": "yes",
        "adverse_parties": "Mark Davis", "incident_date": {"year": 2026, "month": 9, "day": 30},
        "narrative": "Rear-ended at a red light.", "incident_type": "motor_vehicle", "incident_state": "florida",
        "incident_location": "Orlando", "injuries": "neck and back pain", "treatment": "er_or_hospital",
        "police_report": "yes", "government_involved": "no", "vehicle_role": "driver", "other_vehicle": "personal",
        "on_the_job": "no", "seat_belt": "yes", "um_coverage": "not_sure",
    }
    STATE = {"disposition": "pending_signature", "conflict_status": "clear",
             "conflict_names": ["Ana Lopez", "Mark Davis"], "flags": {"sol_urgent"}}

    def record(self, **overrides):
        return intake.build_record({**self.FIELDS, **overrides}, self.STATE, "call-1", datetime(2026, 10, 8, 14, 2))

    def test_record_is_grouped_by_decision_driver(self):
        record = self.record()
        self.assertEqual("Ana Lopez", record["caller"]["name"])
        self.assertEqual("2026-09-30", record["incident"]["date"])
        self.assertEqual("yes", record["liability"]["seat_belt"])
        self.assertEqual("not_sure", record["coverage"]["um_coverage"])
        self.assertEqual("Mark Davis", record["parties"]["adverse"])
        self.assertEqual(["sol_urgent"], record["flags"])
        self.assertEqual("not_needed", record["conflicts"]["recheck"])

    def test_unsure_counts_as_collected(self):
        self.assertEqual([], self.record()["completeness"]["critical_missing"])

    def test_missing_fields_are_listed(self):
        completeness = self.record(injuries=None)["completeness"]
        self.assertEqual(["injuries"], completeness["critical_missing"])
        self.assertIn("witnesses", completeness["important_missing"])
        # optional critical fields (only apply sometimes) are never "missing"
        self.assertNotIn("other_parties", completeness["critical_missing"])
        self.assertNotIn("first_treatment_date", completeness["critical_missing"])

    def test_partial_call_still_produces_a_record(self):
        record = intake.build_record({"caller_name": "Sam"}, {}, "call-2", datetime(2026, 10, 8))
        self.assertEqual("partial_intake", record["disposition"])
        self.assertEqual("Sam", record["caller"]["name"])


class TestNamedParties(unittest.TestCase):
    def test_nobody_answers_are_not_names(self):
        for answer in ("", None, "none", "None.", "nobody", "No one", "No one else was involved", "nobody else",
                       "No other parties", "unknown", "Not sure", "I don't know", "N/A", "There was no one else"):
            self.assertEqual("", intake.named_parties(answer), answer)

    def test_names_are_kept(self):
        # a wrongly dropped name would skip a conflict re-check, so anything name-like is kept
        for answer in ("Coastal Freight Lines", "his employer, Coastal Freight Lines", "Nothing Bundt Cakes",
                       "Noone Construction", "Nobody's Diner", "Northside Hospital", "No Frills Market"):
            self.assertEqual(answer, intake.named_parties(answer), answer)


class TestDetailFlags(unittest.TestCase):
    def flags(self, **fields):
        return qualification.flags(fields, date(2026, 10, 8))

    def test_other_vehicle_flags(self):
        self.assertEqual({"commercial_vehicle"}, self.flags(other_vehicle="commercial_or_work"))
        self.assertEqual({"rideshare"}, self.flags(other_vehicle="rideshare"))
        self.assertEqual({"hit_and_run"}, self.flags(other_vehicle="hit_and_run"))
        self.assertEqual(set(), self.flags(other_vehicle="personal"))

    def test_caller_detail_flags(self):
        self.assertEqual({"on_the_job"}, self.flags(on_the_job="yes"))
        self.assertEqual({"statement_given"}, self.flags(insurer_contact="gave_statement"))
        self.assertEqual({"prior_similar_injury"}, self.flags(prior_similar_injury="yes"))
        self.assertEqual({"no_seat_belt"}, self.flags(seat_belt="no"))
        self.assertEqual(set(), self.flags(seat_belt="not_sure", insurer_contact="contacted_only"))


if __name__ == "__main__":
    unittest.main()
