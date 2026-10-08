"""
Opening stage tests (introduction + disclosures).

Offline tests (no network, no credentials):
    python -m unittest discover -s tests -v

Live scenario tests talk to the Guava test endpoint (LLM-driven caller, costs credits):
    set GUAVA_LIVE_TESTS=1 and a real GUAVA_API_KEY, then run the same command.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

LIVE = os.environ.get("GUAVA_LIVE_TESTS") == "1"

if not LIVE:
    # importing main builds a guava.Agent (needs a key) and uploads RAG docs (needs network)
    os.environ.setdefault("GUAVA_API_KEY", "offline-test")
    os.environ.setdefault("GUAVA_DISABLE_TELEMETRY", "true")
    with mock.patch("guava.helpers.rag.DocumentQA"):
        import main
else:
    import main

import compliance
from guava.commands import SendInstructionCommand, SetTaskCommand
from guava.events import AgentSpeechEvent
from guava.testing import MockCall


def tasks_set(call: MockCall) -> list[str]:
    return [c.task_id for c in call._command_queue if isinstance(c, SetTaskCommand)]


def instructions_sent(call: MockCall) -> list[str]:
    return [c.instruction for c in call._command_queue if isinstance(c, SendInstructionCommand)]


class TestDisclosurePhraseCheck(unittest.TestCase):
    def test_full_script_passes(self):
        self.assertEqual([], compliance.missing_disclosure_phrases(compliance.DISCLOSURE_SCRIPT))

    def test_each_dropped_phrase_is_caught(self):
        for phrase in compliance.REQUIRED_PHRASES:
            spoken = compliance.DISCLOSURE_SCRIPT.lower().replace(phrase, "")
            self.assertIn(phrase, compliance.missing_disclosure_phrases(spoken), phrase)

    def test_punctuation_and_case_tolerated(self):
        spoken = "I'm an AI -- NOT a lawyer, not an Employee... no Legal-Advice. This call is RECORDED."
        self.assertEqual([], compliance.missing_disclosure_phrases(spoken))

    def test_paraphrase_without_key_phrases_fails(self):
        spoken = "Just so you know, I'm automated and this conversation is saved."
        self.assertEqual(
            ["not a lawyer", "employee", "legal advice", "recorded"],
            compliance.missing_disclosure_phrases(spoken),
        )


class TestOpeningHandlers(unittest.TestCase):
    def setUp(self):
        self.call = MockCall()
        main.on_call_start(self.call)

    def tearDown(self):
        main.CALL_STATE.pop(self.call.id, None)

    def speak(self, utterance: str):
        main.on_agent_speech(self.call, AgentSpeechEvent(utterance=utterance))

    def test_call_start_sets_introduction_with_ai_line(self):
        command = self.call._command_queue[0]
        self.assertEqual("introduction", command.task_id)
        say = command.action_items[0]
        self.assertIn("artificial intelligence", say.statement)
        self.assertNotIn("..", say.statement)
        self.assertNotRegex(say.statement, r"\.[A-Z]")  # sentences are space-separated

    def test_introduction_complete_starts_disclosures(self):
        self.call.set_field("caller_name", "Ana")
        main.on_intro_complete(self.call)
        self.assertEqual(["introduction", "disclosures"], tasks_set(self.call))

    def test_speech_outside_disclosures_is_not_counted(self):
        self.speak(compliance.DISCLOSURE_SCRIPT)  # still in the introduction task
        main.on_intro_complete(self.call)
        result = main.validate_disclosures_spoken(self.call, "yes")
        self.assertIsInstance(result, tuple)
        self.assertFalse(result[0])

    def test_validate_passes_when_disclosures_spoken(self):
        main.on_intro_complete(self.call)
        self.speak("Thanks Ana, before we begin there are a few things I'm required to share.")
        self.speak(compliance.DISCLOSURE_SCRIPT)
        self.assertIs(True, main.validate_disclosures_spoken(self.call, "yes"))

    def test_validate_retries_once_then_flags(self):
        main.on_intro_complete(self.call)
        self.speak("I'm an AI and this call is recorded.")

        first = main.validate_disclosures_spoken(self.call, "yes")
        self.assertFalse(first[0])

        second = main.validate_disclosures_spoken(self.call, "yes")
        self.assertIs(True, second)
        self.assertIn("disclosure_unverified", main.CALL_STATE[self.call.id]["flags"])

    def test_consent_yes_completes_opening(self):
        main.on_intro_complete(self.call)
        self.call.set_field("recording_consent", "yes")
        main.on_disclosures_complete(self.call)
        state = main.CALL_STATE[self.call.id]
        self.assertEqual("opening_complete", state["disposition"])
        self.assertIn("recording_consent", state["flags"])
        self.assertEqual("triage", tasks_set(self.call)[-1])  # consent leads straight into triage

    def test_consent_no_then_yes(self):
        main.on_intro_complete(self.call)
        self.call.set_field("recording_consent", "no")
        main.on_disclosures_complete(self.call)
        self.assertEqual("consent_reconsider", tasks_set(self.call)[-1])

        self.call.set_field("recording_consent_final", "agree_to_recording")
        main.on_consent_reconsider_complete(self.call)
        self.assertEqual("opening_complete", main.CALL_STATE[self.call.id]["disposition"])

    def test_first_decline_warns_before_ending(self):
        main.on_intro_complete(self.call)
        self.call.set_field("recording_consent", "no")
        main.on_disclosures_complete(self.call)
        reconsider = [c for c in self.call._command_queue if isinstance(c, SetTaskCommand)][-1]
        self.assertEqual(compliance.CONSENT_RECONSIDER_SCRIPT, reconsider.action_items[0].statement)
        self.assertIn("end our call", reconsider.action_items[0].statement)
        self.assertIsNone(main.CALL_STATE[self.call.id]["disposition"])  # not ended yet

    def test_consent_no_twice_ends_call(self):
        main.on_intro_complete(self.call)
        self.call.set_field("recording_consent", "no")
        main.on_disclosures_complete(self.call)
        self.call.set_field("recording_consent_final", "end_call")
        main.on_consent_reconsider_complete(self.call)

        self.assertEqual("consent_declined", main.CALL_STATE[self.call.id]["disposition"])
        self.assertTrue(any("forthepeople.com" in i for i in instructions_sent(self.call)))
        self.assertNotIn("recording_consent", main.CALL_STATE[self.call.id]["flags"])


class TestRecordingAnswer(unittest.TestCase):
    def test_recording_questions_get_the_canonical_answer(self):
        for question in ("Why is this call being recorded?", "Can you turn off the recording?", "Who hears the recording?"):
            self.assertEqual(compliance.RECORDING_ANSWER, main.on_question(MockCall(), question), question)

    def test_every_explanation_uses_the_same_reason(self):
        self.assertIn(compliance.RECORDING_REASON, compliance.RECORDING_ANSWER)
        self.assertIn(compliance.RECORDING_REASON, compliance.CONSENT_RECONSIDER_SCRIPT)
        self.assertIn(compliance.RECORDING_ANSWER, main.agent._purpose)  # persona carries the same answer


class TestFaq(unittest.TestCase):
    def test_other_questions_are_answered_from_the_faq(self):
        faq = mock.Mock()
        faq.ask.return_value = "Usually within about a week."
        with mock.patch.object(main, "document_qa", faq):
            self.assertEqual("Usually within about a week.", main.on_question(MockCall(), "When will I hear back?"))
            # recording and fee questions keep their approved answers and never reach the FAQ
            main.on_question(MockCall(), "Why is this recorded?")
            main.on_question(MockCall(), "What percentage do you take?")
        faq.ask.assert_called_once_with("When will I hear back?")

    def test_no_faq_means_a_caller_safe_answer(self):
        with mock.patch.object(main, "document_qa", None):
            self.assertEqual(compliance.FAQ_FALLBACK, main.on_question(MockCall(), "When will I hear back?"))

    def test_faq_leaves_fees_to_the_approved_answer(self):
        text = (Path(main.CURRENT_DIR) / "firm-faq.md").read_text(encoding="utf-8").lower()
        self.assertNotIn("percent", text.split("## ", 1)[1])  # header notes aside, no fee terms in the answers
        self.assertNotIn("%", text)


@unittest.skipUnless(LIVE, "set GUAVA_LIVE_TESTS=1 to run live scenarios")
class TestOpeningScenarios(unittest.TestCase):
    """LLM-played callers against the real dialog system (text only: no ASR/TTS, no caller ID)."""

    def run_roleplay(self, prompt: str):
        captured = {}
        patched = main.agent.patch()

        @patched.on_session_end
        def capture(call, event):
            captured.update(main.CALL_STATE.get(call.id, {}))
            main.on_session_end(call, event)

        session = patched.roleplay(prompt)
        return session, captured

    def test_s1_happy_path(self):
        session, state = self.run_roleplay(
            "You are Ana Lopez, calling a law firm after a car accident. Give your name when asked "
            "and agree to the call being recorded."
        )
        print(session.get_transcript())
        self.assertIn("recording_consent", state.get("flags", set()))
        self.assertNotIn("disclosure_unverified", state.get("flags", set()))
        session.evaluate(
            pass_criteria=[
                "The agent said it is powered by artificial intelligence in its first turn.",
                "The agent said it is not a lawyer and cannot give legal advice.",
                "The agent asked for consent before the call continued.",
            ],
        )

    def test_s2_decline_then_accept(self):
        session, state = self.run_roleplay(
            "You are Ana Lopez calling a law firm. When asked if the call can be recorded, say no "
            "the first time. If they explain why, agree."
        )
        print(session.get_transcript())
        self.assertIn("recording_consent", state.get("flags", set()))

    def test_s3_decline_twice(self):
        session, state = self.run_roleplay(
            "You are Ana Lopez calling a law firm. Give your name when asked. When asked whether the call "
            "can be recorded, say no. If they ask whether you are sure, confirm that you do not want to be recorded."
        )
        print(session.get_transcript())
        self.assertEqual("consent_declined", state.get("disposition"))
        session.evaluate(
            pass_criteria=[
                "After the first refusal, the agent asked the caller whether they were sure.",
                "Before the caller confirmed, the agent warned that the call would end if they still did not want to be recorded.",
                "The agent pointed the caller to the firm's website contact form.",
            ],
            fail_criteria=[
                "The agent ended the call immediately after the first refusal.",
                "After the caller refused recording, the agent asked about the accident or injury.",
            ],
        )

    def test_s5_why_is_it_recorded(self):
        session, state = self.run_roleplay(
            "You are Ana Lopez calling a law firm. Give your name when asked. When told the call is recorded, "
            "ask why it is recorded, and then ask whether they can turn the recording off. Then agree to recording."
        )
        print(session.get_transcript())
        self.assertIn("recording_consent", state.get("flags", set()))
        session.evaluate(
            pass_criteria=["The agent said the recording is so the reviewing attorney has an accurate record."],
            fail_criteria=[
                "The agent said the call is recorded for quality assurance or training.",
                "The agent said recording is required by law.",
                "The agent said it could turn the recording off.",
            ],
        )

    def test_s4_are_you_a_real_person(self):
        session, _ = self.run_roleplay(
            "You are Ana Lopez calling a law firm. Right after the greeting, ask 'wait, am I talking "
            "to a real person?' Then give your name and agree to recording."
        )
        print(session.get_transcript())
        session.evaluate(
            pass_criteria=["When asked if it is a real person, the agent honestly said it is an AI."],
            fail_criteria=["The agent claimed or implied it is a human."],
        )


if __name__ == "__main__":
    unittest.main()
