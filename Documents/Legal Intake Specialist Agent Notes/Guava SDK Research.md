# Guava SDK Research — Building a Legal Intake Specialist Voice Agent

**Date:** 2026-10-07
**SDK version examined:** `guava-sdk` **0.47.0** (Python). Wheel and sdist uploaded to PyPI 2026-10-07T00:20Z. Both were downloaded and read, never executed. The wheel and sdist contain the same `guava/` tree.
**Docs examined:** the local dump `Application/guava-docs.md` (5,236 lines), checked against the live `https://goguava.ai/docs/coding-agent-starter.md`. The only differences are a longer pronunciation paragraph on the live site and two added links (SIP Transfers, Twilio warm transfers). I also read 15 live pages that are not in the dump (see Sources).
**Starter repo examined:** `goguava-ai/guava-starter@main`. That is 404 example `__main__.py` files, every one headed `# SDK conformance: guava-sdk 0.44.0`.

**Scope.** This note covers the Guava SDK only. It does not cover legal domain content; a separate agent is researching that. Its goals are: (1) give a source-cited map of everything the SDK actually provides; (2) judge how the SDK is meant to be used, where it is thin, and which structural product weaknesses are good candidates for the onsite review; (3) propose patterns, grounded in the SDK, for an inbound personal-injury intake line (Morgan & Morgan, Florida) that feels natural but still completes intake reliably. Where the docs and the source disagree, the source wins and the disagreement is flagged. Anything I could not confirm from docs or source is marked **Unverified — test by experiment**.

**Citation legend**
- `D:<line>`: local `Application/guava-docs.md`
- `W:<page>:<line>`: live page `https://goguava.ai/docs/<page>.md`, fetched 2026-10-07 (line numbers refer to the fetched markdown)
- `S:<path>:<line>`: source file inside `guava-sdk` 0.47.0 (e.g. `S:guava/agent.py:695`)
- `ST:<path>:<line>`: `goguava-ai/guava-starter` on `main`
- Confidence: **High** = verified in source (or source plus docs). **Medium** = docs only. **Low** = my inference.

---

## Key takeaways

1. **Mental model: the hosted LLM runs the conversation and your Python code (the "Expert") steers it.** You don't write prompts per turn. You hand the Dialog System *Tasks*: an objective plus a checklist of `Field` / `Say` / free-text items. You react to events and inject context (`send_instruction`, `add_info`, `set_task`). You never see or control the conversational LLM's prompt, model, or temperature (D:11-18, D:205-216).
2. **Handlers for a single call run one at a time, on one thread.** The docs say handlers are "asynchronous" and that `on_question`/`on_action_request` run "in parallel" (D:18, D:216, D:2263-2265, D:2389). In 0.47.0, however, every event for a call is received and dispatched sequentially by one loop (S:guava/agent.py:695-702). A conflict-check API call made inside `on_task_complete` therefore delays that call's `on_question`, `on_escalate`, `on_caller_speech`, and so on until it returns. Worse, `on_call_received` and `on_call_start` run on the *listener* thread *before the call is answered* (S:guava/agent.py:864-889). Slow work there delays pickup for that caller and blocks every other incoming call on the same process. **Slow work has to be offloaded to your own threads.** The deprecated `CallController` API did spawn a thread per event (S:guava/client.py:225-227).
3. **Almost every "control" command is a natural-language request to the LLM, not a guarantee.** `hangup()`, `add_info()` and `set_voicemail_action()` are all implemented as `send_instruction(...)` (S:guava/call.py:153-177, 277-288). The only verbatim or mechanical primitives are `read_script()`, checklist `Say(...)`, `transfer()`/`immediate_transfer()` (dedicated commands), and the typed `Field` values. Compliance-critical behavior (disclosures, no legal advice, emergency routing) has to rest on those primitives, on code-side gates, and on post-call audit, never on prompting alone.
4. **There are useful primitives the docs omit:** `@agent.on_validate(field_key)` and `call.retry_task(reason)` give a deterministic validate-and-re-ask loop at task completion (S:guava/agent.py:321-325, 454-465; S:guava/call.py:271-272). Also undocumented: `call.immediate_transfer()` (S:guava/call.py:208-225), `call.has_field()`, `get_field(key, default)`, `get_variable(key, default)` (S:guava/call.py:95, 183-187), `Runner.call_phone()` (S:guava/runner.py:81-86), the `credit_card_number` and `datetime` field types (S:guava/types/__init__.py:27), `Agent(voice=..., accept_dtmf=...)` (S:guava/agent.py:127), and a native `conference:<id>` transfer target for warm transfers (S:guava/examples/warm_transfer.py:82).
5. **Fields stay available across tasks and survive hang-up.** Each field value is pushed to the SDK as soon as the agent records it, via `ActionItemCompletedEvent` (S:guava/agent.py:511-512). It persists in `call._field_values` for the life of the call. `get_field()` therefore works mid-task, in later tasks, and in `on_session_end` after a caller hangs up. That makes saving partial intakes and building "don't re-ask" checklists (`call.get_field(k) is not None`) both possible. There is **no event or handler** for "field X was just collected", though.
6. **Intake must be split into Tasks, and the branching should happen in code.** `multiple_choice` values are guaranteed to be one of the `choices` (D:1932), so they are the safe routing signal. Beware a footgun: `guava.helpers.llm.IntentRecognizer.classify()` returns `list[SuggestedAction] | None`, not a string (S:guava/helpers/llm.py:88-124). The starter's **legal intake** example compares that list to strings and then passes it to `set_variable` (a `ValueError`), so its case-type branching is broken (ST:examples/legal/intake/__main__.py:165-175). The same bug silently disables emergency triage in the post-discharge example (ST:examples/healthcare/post_discharge_followup/__main__.py:294-296).
7. **Spanish works in the voice layer, but the Expert can't see the active language.** `call.set_language_mode(primary="english", secondary=["spanish"])` auto-switches (D:3427). Spanish and English are the only languages covered by HITRUST/PCI-compliant deployments (D:3483-3485). Only the `grace` voice has non-English clones (D:3174, D:3479-3480). There is **no event that tells your code which language is active**, and transcripts carry no per-turn language marker (D:3473-3474). Verbatim Spanish disclosures therefore need a deterministic branch, e.g. a DTMF "para español oprima 2" or an explicit language field, followed by `set_language_mode(primary="spanish")`.
8. **Mid-call SMS is just an HTTP call and is usable during a live call.** `guava.Client().send_sms(from_number, to_number, message)` has no call coupling (S:guava/client.py:458-468). A starter example texts a payment link mid-call and polls for completion on a background thread (ST:examples/integrations/stripe_take_payment/__main__.py:221-294). It does require A2P 10DLC brand and campaign registration (D:2162-2164; W:outbound-and-sms-permissions:74-105). `next_sms()` blocks while polling and only sees messages that arrive *after `next_sms` itself is called* (S:guava/client.py:494), not after the call started as D:2168 says.
9. **Testing is real, but text-only.** `agent.test()` (scripted turns), `agent.roleplay(prompt)` (an LLM plays the caller), `session.evaluate(pass_criteria, fail_criteria)` (an LLM judge), `agent.patch()` (swap handlers in tests), and `MockCall` (handler unit tests) all exist (W:agent-testing; S:guava/testing/session.py). Test sessions inject text and skip ASR/TTS entirely (S:guava/testing/protocol.py:52-55). They hard-code `from_number=None` (S:guava/agent.py:1293), so there is no testing of noise, silence, barge-in, DTMF or caller ID. `TestSession` exposes the transcript, `executed_actions` and `termination_reason`, but **not field values**, so your handlers have to capture them. On native Windows Python, `agent.chat()` uses `curses` (S:guava/agent.py:1086), which CPython does not ship on Windows. Use `agent.test()`/`roleplay()` or WSL.
10. **Two defaults need overriding:** (a) if you don't register `on_escalate`, an *agent-initiated* escalation is told to "apologize … and hang up the call immediately" (S:guava/agent.py:620-621); (b) if you register `on_action_request`, `on_escalate` stops receiving *caller* requests for a human (D:3037-3039). For a law firm's intake line you want a registered `on_escalate` and an explicit "speak to a person" intent.
11. **Compliance defaults to watch for a law firm:** server-mode `DocumentQA` warns at runtime that it "does not carry the data compliance guarantees available in the rest of Guava" (S:guava/helpers/rag.py:78-86). This is not in the docs. Without a `namespace`, its reconcile step **deletes every org document not in its own set** (S:guava/helpers/server_rag.py:339-355). `sensitive=True` does not keep values out of diagnostic data (D:1846-1848). SDK telemetry is on by default and uploads method names plus exception `repr`s (S:guava/telemetry.py:32-46, 159-164); disable it with `GUAVA_DISABLE_TELEMETRY=true`. INFO logs include caller numbers and question text (S:guava/agent.py:480, 867).
12. **Deployment:** `guava deploy up` builds a sandbox from `guava.toml` with tiers seed/fruit/tree (1/2/4 CPU), replicas, and runtime logs capped at 1,000 lines (W:deployment:142-162; W:cli-reference:299-327). Multiple replicas can listen on the same number and the server assigns each call to one of them (S:guava/listen_inbound.py:1-48). Graceful SIGTERM draining exists only in `guava.Runner` (S:guava/runner.py:88-123), not in bare `agent.listen_phone()`. The health server runs on port 4828 (`/live`, `/ready`) and is gated by `GUAVA_HEALTH_SERVER` (S:guava/health.py:212-260).

---

## Part 1 — SDK reference digest

### 1.1 Architecture and runtime model

| Fact | Evidence | Conf. |
|---|---|---|
| Each call has two halves. The hosted **Dialog System** (audio, STT, LLM, TTS) and your **Expert** (your code), connected by a WebSocket. | D:9-16, D:205-216 | High |
| The Expert makes only outbound connections, so no public server or ngrok is needed and it works behind NAT. | D:218, D:313, D:617 | High (source opens outbound WSS: S:guava/agent.py:673-680) |
| The WebSocket layer is resumable. It uses sequence numbers, a retransmission buffer, and ack/ping. It makes up to 10 reconnect attempts with backoff of 1s, then 5s, then 10s. If the server reconnects 15 or more times in a minute it is treated as broken. | S:guava/socket/client.py:69, 110-117, 137-206, 226-230 | High |
| Each call socket has a hard 5-hour maximum age. | S:guava/agent.py:679; S:guava/socket/client.py:233-237 | High |
| **Per-call dispatch:** one thread receives events and dispatches them serially. A second thread drains your command queue to the socket. Commands are thread-safe because they go through `queue.Queue`. | S:guava/agent.py:682-702; S:guava/call.py:70, 179-181 | High |
| **Listener:** `on_call_received` and `on_call_start` (inside `_init_call`) run on the listen loop. `AnswerCall` is sent only after `on_call_start` returns, and an exception in `on_call_start` declines the call. | S:guava/agent.py:864-889 | High |
| At call init the SDK sends the persona (name, purpose, organization, voice, pronunciations, speed). It also sends `RegisteredHooksCommand`, which tells the server which optional hooks exist (`has_on_question`, `has_on_action_requested`, `has_on_escalate`, `accept_dtmf_for_numbers`, `has_on_agent_dtmf`). | S:guava/agent.py:627-646; S:guava/commands.py:115-122 | High |
| The server adapts to the hooks you register. All hooks are optional. | D:224-226 | Medium (the hook flags confirm the mechanism; what the server does with them is opaque) |
| `set_task` may be called from any handler "or at any time (even on another thread)". | D:1545 | High (the queue is thread-safe; starter examples do this: ST:examples/integrations/stripe_take_payment/__main__.py:251-257) |

### 1.2 `Agent` construction

The actual signature (S:guava/agent.py:127):
```python
guava.Agent(name=None, organization=None, purpose=None, voice=None,
            pronunciations=None, accept_dtmf=True, speech_speed=None)
```
- The docs' signature omits `voice` and `accept_dtmf` (D:1413-1428). `voice` was added in May 2026 according to the release notes (W:release-notes:426).
- `purpose` is meant to be one line; the docs say to steer with Tasks, not a large prompt (D:47, D:90, D:532).
- `pronunciations` takes IPA wrapped in `/.../` or a phonetic respelling (D:1456). The live docs add inline SSML `<phoneme>` support (live coding-agent-starter diff; W:release-notes:88). The CLI command `guava say <text> -v <voice> -l <language>` previews TTS (W:cli-reference:289-297).
- `speech_speed` accepts `"x-slow" | "slow" | "medium" | "fast" | "x-fast"` and is validated at construction (S:guava/commands.py:78-93). `call.set_persona(speech_speed=...)` changes it per call, taking effect on the next utterance (D:3180).
- Voices: `grace` (default, Southeastern U.S. female), `andie`, `otto`, `colin`, `kyle`, `kate`, `jack`. **Only `grace` supports non-English languages** (D:3174).
- Constructing an `Agent` constructs a `Client()`, which needs credentials at import time. Lookup order: explicit key, then the deploy token at `/var/run/secrets/guava/token`, then `GUAVA_API_KEY`, then CLI login (S:guava/client.py:62-77; S:guava/auth.py:31). The first `Client` also calls the SDK deprecation-check endpoint (S:guava/client.py:79-100).

### 1.3 Tasks and checklists

`call.set_task(task_id, objective="", checklist=None, completion_criteria="")` (S:guava/call.py:227-269; D:1511-1525)
- At least one of `objective` or `checklist` is required (assert at S:guava/call.py:234).
- Checklist item types: `Field` collects typed data; `Say` is spoken verbatim; a plain `str` becomes a `Todo`, an instruction to the agent (S:guava/call.py:240-260; D:1552-1564). `guava.Todo` is exported but not documented (S:guava/__init__.py:2).
- The docs call the checklist an "ordered list of items" (D:1519). Whether the agent will capture a later field that the caller volunteers early is **Unverified** (see §7).
- `completion_criteria` is free text describing when the task is done (D:1522-1524). Example usage: S:guava/examples/edge/barista.py:67; ST:…/cash_advance (SDK example S:guava/examples/cash_advance.py:63).
- **Completion:** the server sends `TaskCompletedEvent(task_id)` (S:guava/events.py:93-95). Before your handler runs, the SDK calls any `on_validate` handlers for that task's fields. If any of them return `(False, msg)`, it calls `call.retry_task(reason=" ".join(errors))` and **does not** call `on_task_complete` (S:guava/agent.py:454-465).
- If `on_task_complete` raises, the SDK sends `ExpertErrorCommand("… the task has failed.")` to the agent (S:guava/agent.py:475-478). How the agent responds to that is **Unverified**.
- `on_task_complete` has two forms: per-task `@agent.on_task_complete("id")` with signature `(call)`, or a generic bare decorator with signature `(call, task_id)`. Mixing them raises `TypeError` (D:2498-2503; S:guava/agent.py:295-319). `on_reach_person` is implemented as `on_task_complete("reach_person")` (S:guava/agent.py:284-293), so it cannot be combined with a generic handler.
- No handler for a task means a warning is logged ("No handler registered…") (S:guava/agent.py:473-474).

### 1.4 Fields

`guava.Field(key, description='', question='', field_type='text', required=True, choices=[], choice_generator=None, searchable=False, sensitive=False)` (S:guava/types/__init__.py:30-75)

| Type | `get_field()` value | Notes / evidence |
|---|---|---|
| `text` | `str` | D:1929 |
| `date` | `{"year","month","day"}` (ints) | D:1930, D:4003 |
| `datetime` | **Unverified** | Present in source (S:guava/types/__init__.py:27) and in the docs signature (D:1645), but missing from both docs type tables (D:1925-1935, D:3996-4006); added in 0.42.0 (W:release-notes:51) |
| `integer` | `int` | D:1931 |
| `multiple_choice` | `str`, guaranteed to be one of `choices` | D:1932 |
| `calendar_slot` | ISO-8601 `str` | `choices` must be ISO and are validated at construction (S:guava/types/__init__.py:66-70) |
| `digit_sequence` | `str` of digits | D:1934 |
| `cvv` | `str`; always sensitive, plus log and diagnostic suppression for the whole session | D:1875-1884 |
| `credit_card_number` | sensitive, supports DTMF entry | Source only, not in docs (S:guava/types/__init__.py:27; W:release-notes:87) |

- `required=False` lets the agent skip the field if the caller is unwilling (D:1649-1650).
- `question` vs `description`: `question` nudges the exact phrasing, `description` is guidance to the LLM (D:1634-1640).
- `choices` with 10 or more entries triggers a performance warning; use search instead (S:guava/types/__init__.py:73-74). `choices` on a non-choice type raises `TypeError` (S:guava/types/__init__.py:71-72).
- **Search fields:** set `searchable=True` and register `@agent.on_search_query(key)` returning `(matches, fallbacks)` (D:1769-1803; S:guava/agent.py:580-599). The source labels `searchable` "Preview feature. Don't document yet." even though the docs document it (S:guava/types/__init__.py:59-60). In the Python Agent API, `choice_generator` raises `NotImplementedError` (S:guava/call.py:244-245), even though the Python `Field` comment and the TS docs advertise it.
- **Sensitive fields:** best-effort redaction from stored transcripts (spoken and written forms) and silencing of the recording region. This does **not** cover diagnostic or debug data (D:1836-1873). The flag is passed straight through to the server (S:guava/call.py:256).
- **DTMF for numbers:** `Agent(accept_dtmf=True)` is the default and lets callers key in numeric fields (S:guava/agent.py:127, 643; W:release-notes:172).
- **Validation hook (undocumented):** `@agent.on_validate("key")` with signature `def v(call, value) -> True | (False, "message")` (S:guava/agent.py:148, 321-325, 456-465). It runs only at task completion, not per field. Starter examples use it with a `bool | tuple[bool,str]` annotation (ST:examples/insurance/fnol/__main__.py:116-120).

### 1.5 Handlers and events (full list in 0.47.0)

| Handler | Signature | Fires when / payload | Evidence |
|---|---|---|---|
| `on_call_received` | `(call_info) -> AcceptCall() \| DeclineCall()` | Inbound, before answer. Runs on the listener thread. Default: accept. | D:757-774; S:guava/agent.py:192-196, 869-873 |
| `on_call_start` | `(call)` | Inbound and outbound, before answer for inbound. An exception declines the call. | D:1467; S:guava/agent.py:658-659, 877-885 |
| `on_caller_speech` | `(call, CallerSpeechEvent{utterance, utterance_id})` | Every partial transcript. The same `utterance_id` is reused as the transcript is revised. | D:2935-2958; S:guava/events.py:24-33 |
| `on_agent_speech` | `(call, AgentSpeechEvent{utterance, interrupted})` | Each agent utterance, plus whether the caller barged in | D:2843-2860; S:guava/events.py:36-41 |
| `on_question` | `(call, question) -> str` | The agent can't answer from context. The return value is relayed to the caller. Can fire speculatively and repeatedly. An exception returns "An error occurred and the question could not be answered." With no handler, the agent gets "I don't have an answer to that question." | D:2250-2265; S:guava/agent.py:479-491 |
| `on_action_request` | `(call, request) -> SuggestedAction \| list \| None` | The caller asks for an action; the server may confirm it before executing | D:2368-2392; S:guava/agent.py:492-510 |
| `on_action` | per key `(call)` or generic `(call, key)` | Executes the chosen action. **A truthy return value is passed to the agent via `send_instruction`** (undocumented) | S:guava/agent.py:515-537 |
| `on_task_complete` | see §1.3 | | |
| `on_validate` | see §1.4 | Undocumented | S:guava/agent.py:321-325 |
| `on_search_query` | `(call, query) -> (list, list)` | Searchable fields | S:guava/agent.py:273-277 |
| `on_escalate` | `(call, EscalateEvent{requested_by: 'human'\|'agent'})` | The caller asks for a human, or the agent gives up. Not fired for caller requests when `on_action_request` is registered. | D:3018-3039; S:guava/events.py:123-125 |
| (default escalate) | none | With no handler: agent-initiated escalation means "Apologize… and hang up the call immediately"; human-initiated means "no representatives available… continue or call another time". | S:guava/agent.py:620-623 |
| `on_caller_dtmf` (alias `on_dtmf`) | `(call, DTMFPressedEvent{digit, recent_digits})` | Caller keypress | D:2548-2567; S:guava/agent.py:370-385 |
| `on_agent_dtmf` | `(call, AgentDTMFSentEvent{digits, requested_by})` | Agent keypress | D:2643-2667 |
| `on_session_end` | `(call, BotSessionEnded{termination_reason, dnc, pickup})` | `termination_reason` is one of user-hangup, bot-hangup, bot-failure, bot-transfer, voicemail. `dnc` is outbound campaigns only. `pickup` is in source and release notes but not documented. | D:2757-2775; S:guava/events.py:110-115; W:release-notes:19 |
| `on_reach_person` | `(call, outcome)` | Outbound helper | D:3661-3723 |
| `on_outbound_failed` | `(call, OutboundCallFailed{error_code, error_reason})` | Outbound dial failure | S:guava/events.py:104-107 |
| Edge-only (`on_press_enter`, `on_wakeword`, `on_wake`) | | Require `GUAVA_EDGE`. Not relevant here. | S:guava/agent.py:75-86, 395-432 |

**Events that do NOT exist** (important for design). The union in S:guava/events.py:141-164 has no silence or no-input event, no field-collected handler, no language-changed event, no transfer-failed or transfer-answered event, no recording-started event, and no turn-start or end-of-utterance event apart from the test protocol. `ErrorEvent` and `WarningEvent` are only logged (S:guava/agent.py:573-576). `IntentEvent` and `InboundCallEvent` fall through to an "unexpected event" warning (S:guava/agent.py:624-625). Event types newer than the SDK are dropped with a warning (S:guava/events.py:176-185).

### 1.6 The `Call` object: complete command set (0.47.0)

| Method | What it actually does | Deterministic? | Evidence |
|---|---|---|---|
| `call.id`, `call.call_info` | Session id. `call_info` is a `PSTNCallInfo{from_number (may be None for blocked IDs), to_number, caller_id}`, `WebRTCCallInfo`, or `SipCallInfo{from_aor, sip_code, sip_headers}` | — | S:guava/call.py:78-84; S:guava/types/call_info.py:168-225 |
| `set_task(...)` | `SetTaskCommand` | Mechanism yes; behavior is the LLM's | S:guava/call.py:227-269 |
| `retry_task(reason)` | `RetryTaskCommand`. **Undocumented** | Mechanism yes | S:guava/call.py:271-272 |
| `send_instruction(text)` | `SendInstructionCommand`. Real-time context or nudge without replacing the task | No (prompt) | S:guava/call.py:280-281; D:3226-3256 |
| `add_info(label, info)` | **Just** `send_instruction("Here is some information about the following topic …" + json.dumps(info))` | No (prompt) | S:guava/call.py:277-278 |
| `hangup(final_instructions="")` | **Just** `send_instruction("Start ending the conversation … hang up the call.")`. There is no hard hang-up command. | **No** | S:guava/call.py:283-288; D:3576 ("soft hangup") |
| `transfer(destination, instructions=None)` | `TransferCommand(soft_transfer=True)`. Agent announces, then bridges. Phone number or SIP URI. | Mechanism yes | S:guava/call.py:189-206; D:3520-3540 |
| `immediate_transfer(destination, final_script=None)` | `TransferCommand(soft_transfer=False)`. Ignores turn-taking. **Undocumented** in reference pages (only in release notes). | Yes | S:guava/call.py:208-225; W:release-notes:122 |
| `read_script(script)` | `ReadScriptCommand`. Verbatim. Docs say it is the very first words, before any LLM turn. | Yes (verbatim) | S:guava/call.py:274-275; D:3866, D:3879 |
| `set_persona(organization_name, agent_name, agent_purpose, voice, pronunciations, speech_speed)` | `SetPersona`. Python also accepts `pronunciations`, which the docs omit. | Yes | S:guava/call.py:133-151; D:3116-3182 |
| `set_language_mode(primary="english", secondary=None)` | `SetLanguageMode`. Languages: english, spanish, french, german, italian. | Yes | S:guava/call.py:101-111; S:guava/types/__init__.py:25 |
| `set_variable(k, v)` / `get_variable(k, default=None)` (+ aliases `set_var`/`get_var`) | Stored locally **and** sent to the server as `SetVariableCommand`. `v` must be JSON-serializable or `ValueError` is raised. | Yes | S:guava/call.py:86-99 |
| `get_field(k, default=None)`, `has_field(k)` | Read from the locally mirrored field dict | Yes | S:guava/call.py:183-187 |
| `set_voicemail_action(hangup=False, message=None)` | **Just** `send_instruction(...)`. Mutually exclusive with `reach_person`. | No | S:guava/call.py:153-177 |
| `reach_person(contact_full_name, *, greeting, voicemail_message, voicemail_hangup, outcomes)` | Built entirely on `set_task("reach_person", …)`. Outbound use. | — | S:guava/call.py:295-405 |
| `set_agent_dtmf(enabled)`, `send_dtmf(digits)` | Agent DTMF. Raises on WebRTC calls. | Yes | S:guava/call.py:113-130 |
| (no public method) `SendCallerTextCommand` | A "send-caller-text" command exists in the protocol but no `Call` method sends it | — | S:guava/commands.py:150-152 |

### 1.7 Channels and `Runner`

- `listen_phone(number)`, `listen_webrtc(code=None)` (creates a 1-hour temporary code), `listen_sip("guavasip-…")`, `call_phone(from, to, variables)`, `call_local(variables)` (local audio via a 5-minute WebRTC code), `attach_campaign(code)`, `chat(variables)`, `test(variables)`, `roleplay(prompt, variables)` (D:1481-1495; S:guava/agent.py:714-765, 904-1004, 1011-1307).
- `test_audio(input_wav, output_wav, variables)` is a **preview** feature that injects a WAV as the caller's microphone and captures the agent's audio (S:guava/agent.py:743-765; W:release-notes:100).
- `Runner` hosts multiple agents and channels: `listen_phone/listen_webrtc/listen_sip/attach_campaign/call_phone`, then `run()`. On the first SIGINT/SIGTERM it **drains**: stops accepting calls and waits for in-flight calls. A second signal force-exits (D:1973-1999; S:guava/runner.py:17-154). `Runner.call_phone` is "safe to call from handlers while running" (S:guava/runner.py:81-86).
- SIP: whitelist your peer, then `sip.goguava.ai`, IP 136.118.29.109, PCMU/PCMA (D:5046-5118). For SIP transfers Guava sends a `REFER`, so the destination is dialed by the transferee or ITSP and must be routable from there. URI and header parameters (`X-…`, `User-to-User`) can carry intake context (W:sip-transfers:7-114). Incoming SIP headers appear in `call.call_info.sip_headers` (S:guava/types/call_info.py:184-192).
- WebRTC widget: a `<script>` embed with a `grtc-` code and an optional chat panel with text input (W:webrtc-widgets). Codes come from `guava widget [--ttl]` or `Client.create_webrtc_agent(ttl)`.

### 1.8 Transfers: warm vs. cold

- `transfer()` is a **soft cold transfer**: the agent tells the caller, then bridges. The person receiving the call gets no briefing (D:3522). `immediate_transfer()` cuts in without waiting for the turn to finish (S:guava/call.py:208-225).
- **Warm transfer pattern (SDK example):** the inbound agent completes intake, then `set_task("stall_customer", …)`. `runner.call_phone(outbound_agent, …, variables={conference_id, call_reason})` places an outbound call. The outbound agent briefs the human, and on readiness **both** calls `transfer(f"conference:{conference_id}")` (S:guava/examples/warm_transfer.py:30-89). The `conference:` destination scheme appears only in this example; the docs version uses Twilio conferences (W:twilio-warm-transfers). Rough edge: if the human never answers there is no timeout or `on_outbound_failed` handling, so the caller is stalled indefinitely.
- There is **no transfer-failure event**. A successful transfer ends the session with `termination_reason="bot-transfer"` (D:2768).

### 1.9 Outbound and campaigns (relevant only for follow-ups)

Campaigns handle retries, calling windows, concurrency, DNC skipping, and contact `data` (which becomes variables) (D:4862-5032; W:cli-reference:257-279). Outbound requires the Outbound Dialing registration (KYC with EIN) (W:outbound-and-sms-permissions:50-64). "Agentic Tenacity" sends a pre-call SMS, and that is the only modality so far (W:agentic-tenacity:42-70). Not needed for the inbound MVP, but it is how next-day document-chase calls would be built.

### 1.10 SMS

- `Client.send_sms(from_number, to_number, message) -> None` sends via `POST /v1/send-sms`. It raises if the number isn't owned or isn't SMS-enabled (D:2145-2164; S:guava/client.py:458-468; W:messages-api:11-58).
- `Client.next_sms(from_number, to_number, *, timeout=60.0, poll_interval=2.0) -> dict | None` polls `GET /v1/messages`. **Its start time is the moment `next_sms` is called** (S:guava/client.py:494), not the start of the call (D:2168).
- **During a live call:** nothing in the SDK prevents it, and a starter example does exactly this (ST:examples/integrations/stripe_take_payment/__main__.py:220-294, which texts a link, instructs the agent, and polls in a daemon thread). Because dispatch is serial (§1.1), call `next_sms` or any polling **only from your own thread**.
- Prerequisites: SMS Brand and SMS Campaign (A2P 10DLC) registrations per use case. Common rejections: no public URL shorteners, an SMS-specific opt-in, STOP/HELP responses (W:outbound-and-sms-permissions:74-119). Whether a new or trial org can send SMS before registration completes is **Unverified**.

### 1.11 Knowledge base / RAG

- Retrieval is triggered only through your `on_question` handler, which the agent calls when it can't answer from context. You return a string (D:2250-2265). For immediate answers, pre-load context with `add_info` (D:2261), which is just an instruction (§1.6).
- `DocumentQA(store=None, documents=None, ids=None, chunk_size=5000, chunk_overlap=200, instructions=None, *, generation_model=None, server_rag=None, namespace=None)` (S:guava/helpers/rag.py:248-262).
  - **Server mode** (no `store`): the full document context is sent server-side and `k` is ignored (D:4446). It emits a `UserWarning` saying it is "intended for testing and simple use cases" and "does not carry the data compliance guarantees available in the rest of Guava" (S:guava/helpers/rag.py:76-86). The warning is not in the docs.
  - **Namespace hazard:** reconcile without a namespace treats *all* org documents as its scope and **deletes any not in its list** (S:guava/helpers/server_rag.py:339-355). `ask()` on an instance with no tracked keys queries all org documents (S:guava/helpers/server_rag.py:390-396). The docs only say namespace is "required when running multiple instances concurrently" (D:4440-4442).
  - **Local mode:** pass `store` (`ChromaVectorStore`, `LanceDBStore`, `PgVectorStore`, `PineconeVectorStore`) plus `generation_model` (OpenAI or Gemini wrappers) (D:4456-4465). Install with extras, e.g. `guava-sdk[chromadb]` (PyPI `provides_extra`).
- `guava.helpers.llm.generate(prompt, json_schema=None)` is a public call to Guava's LLM endpoint with schema-constrained output and a 60-second timeout (S:guava/helpers/llm.py:14-55). It is handy for in-handler classification without a separate LLM vendor. Also in `helpers.llm`: `IntentRecognizer`, `DatetimeFilter` (the current version; the docs show the deprecated OpenAI one, D:1054 and D:4489), and an undocumented `DateRangeParser` (S:guava/helpers/llm.py:181-222).

### 1.12 Recording, transcripts, post-call data, logging

- Recordings and transcripts are server-side. Get them via the CLI (`guava conversations list|get|transcript|recording`) or REST: `GET /v1/conversations[/{id}[/transcript|/recording]]` and `DELETE /v1/conversations/{id}` (W:cli-reference:228-246; W:conversations-api). A transcript turn is `{speaker: HUMAN|AGENT, text, offset_ms}`. The metadata includes `termination_reason` and `duration_sec`. **Collected field values, task outcomes and handler errors are not in the Conversations API.** You must persist them yourself.
- There is no SDK switch to disable or announce recording, and no recording-consent primitive. Disclosure is your script (Medium, inferred from absence across the docs and source).
- Your own transcript: accumulate `on_caller_speech` (collapsing partials by `utterance_id`) and `on_agent_speech` per `call.id`, as Guava's benchmark bot does (S:guava/benchmark-bots/info_extraction.py:16-24).
- Logging: `guava.logging_utils.configure_logging()` with `LOG_LEVEL` (default INFO) and `NO_COLOR` (S:guava/logging_utils.py:41-78). INFO logs include `call_info` with phone numbers (S:guava/agent.py:867), question text (S:guava/agent.py:480), and field **keys** only (S:guava/agent.py:513-514). DEBUG logs every queued command including instructions (S:guava/call.py:181). Deployed logs: `guava deploy logs -n` (max 1,000 lines) (W:deployment:143).
- Telemetry: on by default. It records method-call names and exception `repr`s and uploads them to `/v1/upload-telemetry`. Disable with `GUAVA_DISABLE_TELEMETRY=true` (S:guava/telemetry.py:32-46, 94-96, 159-164).

### 1.13 Async model, latency, long-running work

- The docs' claims (D:18, D:216, D:577) mean the **caller** doesn't hear dead air while your handler runs, because the Dialog System keeps talking. That holds as far as it goes. But see §1.1: the Expert processes one event at a time per call, and `on_question`/`on_search_query` must *return* their result (S:guava/agent.py:483-484, 589), so they hold the dispatch thread for their whole duration.
- There is no SDK timeout on handlers and no built-in filler or "please hold" primitive. Fillers come from the Dialog System (opaque) or your own `send_instruction`. `ReachPersonOutcome.next_action_preview` hints at a "Let me just …" stalling technique used internally (S:guava/call.py:33-47).
- The helper HTTP timeouts are LLM 60s and RAG ask 120s (S:guava/helpers/llm.py:52; S:guava/helpers/server_rag.py:313). Wrap your own calls with explicit timeouts.

### 1.14 Testing tools

- `MockCall(session_id=None, call_info=PSTNCallInfo(+1555…))` with `.set_field()`. Commands are captured in `._command_queue` (a list, private) (S:guava/testing/mocks.py:14-38).
- `agent.test(variables)` is a context manager that yields a `TestSession` with `say()`, `wait_for_turn()`, `wait_for_end()`, `recv()`, `get_transcript()`, `evaluate(pass_criteria, fail_criteria)` (an LLM judge that raises `AssertionError`), `executed_actions`, `termination_reason` and `id` (S:guava/testing/session.py:120-230; S:guava/agent.py:1255-1307).
- `agent.roleplay(prompt, variables)` loops: wait for the turn, then an LLM decides to `speak` or `hangup` based on the transcript (S:guava/agent.py:1011-1073).
- `agent.patch()` clones the agent so handlers can be overridden (S:guava/agent.py:1235-1253).
- Limitations (source): utterances are injected as ASR text (S:guava/testing/protocol.py:52-55); the test call has `from_number=None` (S:guava/agent.py:1293); `TestSession` exposes no field values; `evaluate` is an LLM judge and therefore non-deterministic.
- Audio and noise: `test_audio` (preview), plus a benchmark harness that sweeps SNR with car noise. Guava's own numbers show accuracy falling from about 97% when clean to 77% at 5 dB and 37% at 0 dB, and last names, DOB and email fail first (S:guava/benchmark-bots/README.md:1-60). That is relevant for callers phoning from cars or ERs.

### 1.15 Deployment

- `guava.toml`: `project_id, org_id, name, call_direction, base_image (python-sandbox:3.10–3.14 | node-sandbox:22/24/26), phone_number, tier (guava-seed|fruit|tree), replicas` (W:cli-reference:299-344). The user's file also has `enable_healthcheck = true`, which is **not** in the documented schema.
- `guava deploy up [--rebuild]`, `down`, `purge`, `scale N`, `status`, `logs -n`, `build-logs`, `ls`, `changed`; `guava numbers buy` injects `GUAVA_AGENT_NUMBER`; `guava update` changes tier or base image (W:cli-reference:10-41, 216-226).
- Dependencies are detected from `uv.lock`/`pyproject.toml`/`requirements.txt` (W:cli-reference:346-358). The upload **excludes hidden files**, `__pycache__`, `node_modules` and `guava.toml` (W:cli-reference:377). The entry point must be `main.py` (W:cli-reference:374).
- Secrets: the API key and phone number are "injected securely at runtime" (W:deployment:92). The release notes say "`guava deploy` can now use `.env` files to mount secrets" (W:release-notes:430), but the Deployment page doesn't describe it and hidden files are excluded from upload. **Unverified** (see §7).
- Sandboxes allow outbound internet but no inbound connections. `/tmp` is ephemeral (W:deployment:91, 148-152). So webhook-style integrations (e.g. e-sign completion webhooks) cannot be received in a Guava-hosted sandbox. Poll instead, or host that part elsewhere (Low, an inference from "no one can connect into your sandbox").
- Health: `HealthServer` on `0.0.0.0:4828` serving `/live` and `/ready` when `GUAVA_HEALTH_SERVER` is true (S:guava/health.py:212-260). Readiness becomes true on `ListenStarted` (S:guava/agent.py:855-856).
- Replicas: each replica opens a listen socket. The server sends `IncomingCall`, listeners `ClaimCall`, and the server `AssignCall`s to one of them (S:guava/listen_inbound.py:1-48). `ListenStarted.other_listeners` reports the count (S:guava/agent.py:858).

### 1.16 Multilingual

See takeaway 7. Also: when the caller speaks a configured secondary language, the system switches TTS voice automatically (D:3479). Transcripts are not translated (D:3473). Field values captured from Spanish speech (e.g. `text` narratives) may come back in Spanish. That is **Unverified** and matters for English-speaking intake reviewers.

### 1.17 Limits, quotas, pricing

- Pricing (https://goguava.ai/pricing, fetched 2026-10-07): Starter free (500 min/yr, $0.15/min overage, "watermarked / limited concurrency"); Build $149/mo (1,500 min/yr, $0.14/min); Scale $499/mo (7,000 min/yr, $0.13/min); Enterprise custom with dedicated infrastructure and SLAs. The page claims SOC 2 Type II, PCI DSS and HITRUST i1 on every account.
- Documented limits: call socket max age 5h (source), deploy logs max 1,000 lines, conversation list page size 100, webrtc temp code TTLs (1h listen, 5m local). Concurrency limits per tier are **not documented numerically**.

---

## Part 1b — Docs-vs-source discrepancies and starter-repo misuses

### Docs vs. source (0.47.0)

| # | Docs say | Source shows | Impact |
|---|---|---|---|
| 1 | Handlers are async and off the dialog thread; `on_question` and `on_action_request` are invoked "in parallel" (D:18, D:216, D:2265, D:2389) | Per-call events are dispatched serially on one thread (S:guava/agent.py:695-702). `on_call_received`/`on_call_start` block the listener before answer (S:guava/agent.py:864-889). | Slow handlers delay all later handling for that call and pickup of other calls. |
| 2 | `hangup()` is a "soft hangup" (D:3576) | It is only `send_instruction` (S:guava/call.py:283-288). No hard hang-up exists. | You can't force-end a call from code. |
| 3 | `read_script` is the "very first words … before any LLM turn" (D:3866, D:3879) | It is a plain queued command (S:guava/call.py:274-275). Guava's own Edge example uses it **mid-call** to speak a price verbatim (S:guava/examples/edge/barista.py:99-103). | Mid-call verbatim speech is likely possible. **Unverified**. |
| 4 | `set_voicemail_action` presented as a setting (D:3788) | It is an instruction to the LLM (S:guava/call.py:173-177) | — |
| 5 | Agent signature lacks `voice`, `accept_dtmf` (D:1413-1428) | Both exist (S:guava/agent.py:127) | — |
| 6 | Field type tables omit `datetime`, `credit_card_number` | Both present (S:guava/types/__init__.py:27) | — |
| 7 | `searchable` documented as a stable parameter (D:1656-1658) | Source comment says "Preview feature. Don't document yet." (S:guava/types/__init__.py:59-60) | Stability risk. |
| 8 | Python `Field` comment and TS docs advertise `choice_generator` | `set_task` raises `NotImplementedError` for it (S:guava/call.py:244-245) | — |
| 9 | `next_sms` returns messages received "after the call begins" (D:2168) | After the `next_sms` invocation (S:guava/client.py:494) | A reply that arrives before you start waiting is missed. |
| 10 | DocumentQA namespace is only needed for concurrent instances (D:4440-4442) | Without a namespace, reconcile deletes all other org docs (S:guava/helpers/server_rag.py:339-355). Server mode carries a compliance disclaimer (S:guava/helpers/rag.py:78-86). | Data loss and compliance risk. |
| 11 | `on_action_request` example: `key = intent_recognizer.classify(request); return SuggestedAction(key=key) if key else None` using `guava.helpers.llm.IntentRecognizer` (D:2304-2323) | `classify` returns `list[SuggestedAction] \| None` (S:guava/helpers/llm.py:88-124), so `SuggestedAction(key=<list>)` fails pydantic validation | The docs example is broken. |
| 12 | `DatetimeFilter` documented from `guava.helpers.openai` with gpt-5-mini (D:4489-4625) | That class is deprecated; the current one is in `guava.helpers.llm` (S:guava/helpers/openai.py:10-12; S:guava/helpers/llm.py:132-173) | — |
| 13 | Undocumented APIs: `on_validate`, `retry_task`, `immediate_transfer`, `has_field`, `Runner.call_phone`, `Todo`, `pickup`, `conference:` transfers, `test_audio`, `helpers.llm.generate`, `DateRangeParser`, health server, telemetry | Present in source | Useful capability goes undiscovered. |
| 14 | No mention of telemetry | On by default (S:guava/telemetry.py:159-164) | Privacy review item. |
| 15 | `guava.toml` schema (W:cli-reference:308-319) | The user's scaffolded file contains `enable_healthcheck`, which is not in the schema | Docs gap. |
| 16 | Release notes: `.env` secrets for deploy (W:release-notes:430) | CLI reference: hidden files excluded from upload (W:cli-reference:377); Deployment page silent | Unclear how to ship third-party API keys. **Unverified**. |
| 17 | PyPI has 0.47.0 (2026-10-07) | The release notes stop at 0.45.0 (W:release-notes:11-13) | Changes in 0.46–0.47 are undocumented. |

### Starter-repo rough edges / misuses (the brief says these are deliberate)

1. **Legal intake is broken by the IntentRecognizer return type.** `case_type = _case_type_classifier.classify(description)` returns a list; `call.set_variable("case_type", case_type)` then raises `ValueError` because pydantic models aren't JSON-serializable. The task fails, and the `case_type == "family"` branches could never match anyway (ST:examples/legal/intake/__main__.py:164-175; S:guava/call.py:86-88). The same pattern in post-discharge follow-up means **`severity == "emergency"` never fires** (ST:examples/healthcare/post_discharge_followup/__main__.py:294-296).
2. **Legal intake ordering and over-collection:** a full narrative (`brief_description`) and urgency are collected *before* the conflict check (ST:examples/legal/intake/__main__.py:105-137). The conflict check is a substring match on comma-split free text (ST:…/intake/__main__.py:24-32). The conflict detail is logged at WARNING (ST:…:141).
3. **Legal intake `on_question` refuses everything,** including benign FAQs like office hours (ST:…/intake/__main__.py:363-370). Its opener `Say` has no AI or recording disclosure (ST:…:80-86). No `on_escalate` is registered, so agent-initiated escalation hangs up (S:guava/agent.py:620-621). `on_session_end` reads `event.dnc`, which is meaningless inbound (ST:…:419; D:2774). Phone is `text`, not normalized. Nothing is marked `sensitive`.
4. **Global mutable state shared across concurrent calls:** `global account` in the SDK's own `cash_advance.py` (S:guava/examples/cash_advance.py:73, 96). The same pattern appears in 7 starter examples (`grep "global "`). The barista example admits "Only one call is live at a time, so one flag is enough" (S:guava/examples/edge/barista.py:71-72).
5. **SSN last-4 as `integer`** loses leading zeros and isn't `sensitive` (S:guava/examples/cash_advance.py:58-61), against the docs' own advice to use `digit_sequence` with `sensitive=True` (D:1850-1856, D:1871-1873). Only 2 of 404 starter examples use `sensitive=True`.
6. **DOB captured as `text`** and compared by string equality to `"1982-05-11"` (ST:examples/healthcare/patient_intake/__main__.py:111-147; ST:examples/insurance/fnol/__main__.py:107-129). The `date` type exists for exactly this.
7. **The starter docs use a non-existent decorator:** `@agent.on_action_requested` (ST:docs/sdk-reference.md:361-375). The real one is `on_action_request` (S:guava/agent.py:242-243), so the documented one is an `AttributeError`.
8. **Warm-transfer example has no failure path** if the representative doesn't answer (S:guava/examples/warm_transfer.py:28-55). The Stripe example's poll thread keeps running after the caller hangs up (ST:…/stripe_take_payment/__main__.py:260-294).
9. **Version drift:** every starter example is pinned to "conformance 0.44.0" while PyPI is at 0.47.0. The starter README says "65 working demos" but there are 404.
10. The user's own scaffold (`Application/main.py`) uses server-mode `DocumentQA` with a namespace (good), and `listen_phone` directly (so no SIGTERM draining).

---

## Part 2 — Critical assessment

### 2.1 How the SDK is meant to be used, and what it does well

- **Intended mental model:** "Tasks, not prompts." Give the hosted agent a short persona plus a sequence of narrowly scoped goals with typed fields, and react to structured callbacks (D:262-266, D:47). Conversation quality (turn-taking, barge-in, fillers, confirmations, phrasing) belongs to Guava; business logic belongs to you. The Expert is plain code, so any CRM or API is one function call away (D:213-216).
- **Strengths:**
  - Fast path to a working phone agent. There is no telephony plumbing, no public endpoint, and the same code works for phone, WebRTC, SIP, chat and test (D:1481-1495).
  - Typed field extraction with real types (`date` dict, guaranteed `multiple_choice`), plus DTMF entry for numbers.
  - A resilient transport (resumable sockets) and graceful drain in `Runner`.
  - A real test story by voice-agent standards: scripted sessions, LLM roleplay, rubric evaluation and handler patching in ordinary `unittest`/`pytest`.
  - Built-in multilingual switching (English and Spanish are compliance-eligible), sensitive-field redaction in transcripts and audio, and a PCI-grade field type.
  - Transfers to phone or SIP with metadata carried in SIP headers or UUI.

### 2.2 Where it is thin: documentation gaps vs. capability gaps

**Documentation gaps** (the capability exists or is clarified in source):
- The concurrency contract (serial dispatch, listener blocking), plus `on_validate`/`retry_task`, `immediate_transfer`, the `conference:` warm transfer, `has_field`, `Runner.call_phone`, the health server, telemetry, the `pickup` field, field types `datetime`/`credit_card_number`, and the `datetime` return shape.
- The DocumentQA namespace and deletion semantics, and the server-RAG compliance caveat.
- Mid-call `read_script` semantics. SMS during a live call (shown only in a starter example).
- How to ship third-party secrets to a Guava-hosted deploy.
- Release notes lag the published SDK.

**Capability gaps** (absent from source and docs):
- **No deterministic call control from code:** no hard hang-up, no "speak this now, verbatim, and tell me when done" (beyond the opener `read_script` and checklist `Say`), and no acknowledgement events for spoken disclosures.
- **No silence / no-input / end-of-turn events.** Nothing exposes or lets you configure turn-taking (endpointing, max silence, reprompt policy).
- **No field-level event,** so you can't react the moment a single field is captured without polling from another hook.
- **No active-language signal** to the Expert, and no per-turn language tag in transcripts.
- **No transfer outcome events** (answered, busy, failed). After a transfer the Expert loses the call.
- **No access to the conversational LLM:** model choice, guardrail configuration, prompt inspection, or a log of the reasons the agent completed a task.
- **Post-call data:** the Conversations API lacks fields and outcomes, so a CRM sync must be built from handlers.
- **Testing doesn't exercise the voice layer** (ASR errors, noise, silence, barge-in, DTMF, caller ID) except through a preview WAV injector.
- Webhooks can't reach Guava-hosted sandboxes.

### 2.3 Candidate "real structural product weaknesses" (PM framing)

**W1 — The latency contract is misleading: per-call handlers are serialized, and pickup blocks on user code.**
- *What:* The docs promise that handlers are asynchronous and that slow work "does not block or delay the caller" (D:18), and that question and action callbacks run in parallel (D:2265, D:2389). In 0.47.0, every event for a call runs in sequence on one thread (S:guava/agent.py:695-702). `on_call_received`/`on_call_start` run on the shared listener loop before `AnswerCall` (S:guava/agent.py:864-889). The deprecated API spawned a thread per event (S:guava/client.py:225-227), so this is a regression in the new API.
- *Who it hurts:* Every production integration that calls a CRM, conflict system or RAG mid-call. It hurts callers most (a delayed RAG answer, ignored escalation while a slow lookup runs, slower pickup during call spikes), and developers who trust the docs and put lookups in `on_call_start`.
- *Why it matters:* Guava's pitch is that the Expert "can spend time on complex tasks … without the caller ever noticing" (D:216). The architecture delivers that for audio but not for event handling. The failures are load- and latency-dependent, so they appear in production rather than in demos.
- *Urgency:* High. It is cheap to fix (a per-call executor, or a documented concurrency model with an async API) and expensive to discover in the field.
- *Evidence quality:* Source-verified.

**W2 — No deterministic guardrail primitives: "control" means prompting.**
- *What:* `hangup`, `add_info` and `set_voicemail_action` are prompts (S:guava/call.py:153-177, 277-288). There is no hard hang-up, no verified verbatim mid-call speech, no acknowledgement that a disclosure was spoken, no hook that lets code veto or rewrite an agent utterance before TTS, and no way to see or configure the hosted LLM.
- *Who it hurts:* Regulated buyers in legal (must not give legal advice; disclosures), healthcare (emergency routing), financial services (mandated wording). Compliance officers can't sign off on "we asked the model nicely."
- *Why it matters:* Guava markets SOC 2, PCI and HITRUST, and these verticals make up much of the starter catalog. The starter's own emergency-triage and legal-routing examples silently fail (§1b), which shows how fragile LLM-mediated control is even for Guava's own authors.
- *Urgency:* High for regulated-vertical sales. Possible fixes: a hard `end_call()`, a `say_verbatim()` with a spoken-ack event, an `on_before_agent_speech` filter hook, and policy rules ("never discuss X") enforced by the Dialog System.
- *Evidence quality:* Source plus starter-repo evidence.

**W3 — The production-confidence loop is weak: tests skip voice, and post-call data omits outcomes.**
- *What:* Tests inject text past ASR/TTS (S:guava/testing/protocol.py:52-55). Caller ID is fixed at `None` (S:guava/agent.py:1293). Silence, barge-in and DTMF can't be simulated. Field values aren't exposed on `TestSession`. Evaluation is a single LLM-judge call. In production, the Conversations API returns metadata, transcript and audio but not task or field outcomes or handler errors. Logs are capped at 1,000 lines.
- *Who it hurts:* Teams going from demo to production, forward-deployed engineers onboarding a new customer, and QA and compliance reviewers.
- *Why it matters:* The biggest risks in voice agents are acoustic and timing-related (Guava's own benchmark shows a sharp accuracy cliff at low SNR, S:guava/benchmark-bots/README.md). Those are exactly what the test harness can't reach, and there's no first-party way to measure intake completion rates after launch.
- *Urgency:* Medium-high. It slows every enterprise rollout, but it can be mitigated with custom harnesses.

**W4 (secondary) — Safe defaults aren't the default for sensitive data.**
- *What:* Server-side RAG sits outside the compliance guarantees and can delete org documents without a namespace (S:guava/helpers/rag.py:78-86; S:guava/helpers/server_rag.py:339-355). Telemetry is on by default. INFO logs include caller numbers. `sensitive` doesn't cover diagnostics. Compliance-eligible languages are only English and Spanish.
- *Who it hurts:* Law firms (privilege and confidentiality) and anyone with PHI.
- *Urgency:* Medium. Mostly fixable with defaults and documentation.

For the onsite I'd lead with **W1**: it is concrete, source-verified, contradicts an explicit docs claim, has a clear user impact story, and has a cheap fix. **W2** is the strategic one for a legal or healthcare buyer.

---

## Part 3 — Patterns for natural, dynamic, goal-completing intake

Conventions for the sketches below: only verified APIs are used. Anything assumed is marked `# ASSUMED`. Every sketch assumes this shared scaffolding:

```python
import threading, time, logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutTimeout
import guava
from guava import Field, Say
from guava.events import BotSessionEnded, CallerSpeechEvent, AgentSpeechEvent, EscalateEvent, DTMFPressedEvent
from guava.types.call_info import PSTNCallInfo

POOL = ThreadPoolExecutor(max_workers=64)          # handlers dispatch serially -> offload slow work
STATE: dict[str, dict] = {}                          # per-call state keyed by call.id (never globals)
STATE_LOCK = threading.Lock()

def st(call: guava.Call) -> dict:
    with STATE_LOCK:
        return STATE.setdefault(call.id, {"retries": {}, "interrupts": 0, "flags": set()})
```

### P0. Keep handlers fast and offload slow work
- **Problem:** Serial dispatch (W1). A slow handler delays escalation, Q&A and emergency detection for that call. Slow `on_call_start` delays pickup for everyone on that process.
- **Pattern:** Handlers do only O(ms) work. Anything that does I/O goes to `POOL.submit(...)`. When the work finishes, the worker issues commands (`send_instruction`, `set_task`, `transfer`); that is safe because commands go through a thread-safe queue (S:guava/call.py:179-181; D:1545). `on_question` must return synchronously, so bound it with a timeout and return a safe fallback.
- **Primitives:** `ThreadPoolExecutor`, `call.send_instruction`, `call.set_task`, `on_question` return value.
```python
@agent.on_question
def on_question(call, question):
    fut = POOL.submit(answer_firm_faq, question)          # local-mode DocumentQA or curated FAQ
    try:
        return fut.result(timeout=6)
    except FutTimeout:
        return "I don't have that in front of me; I'll note it for the team to follow up."
```
- **Tradeoffs:** More moving parts, and late results from a timed-out future have to be ignored. If the call has ended, commands are queued but never sent (harmless).

### P1. Segmenting the intake into Tasks without it sounding like a form
- **Problem:** One giant checklist produces interrogation, while many tiny tasks produce awkward transitions and repeated questions.
- **Pattern: a few purpose-shaped tasks, built dynamically in code.**
  1. `opener` uses `read_script` for the disclosures (P5).
  2. `triage` covers caller type, language and a safety check: about 2–3 fields, mostly `multiple_choice`.
  3. `conflict_min` collects the minimum identity facts for the conflict check (P6).
  4. `story` is one open `text` field ("tell me in your own words what happened") with `completion_criteria` ("complete once the caller has finished describing the incident; do not interrogate"). Everything structured that the caller volunteers is extracted later by code from this narrative (`helpers.llm.generate` with a JSON schema), not asked again.
  5. `details_<branch>` contains only the fields **still missing**: `[f for f in BRANCH_FIELDS[incident_type] if call.get_field(f.key) is None]`.
  6. `contact_next_steps` covers callback number, best time, text consent and the e-sign link (P9).
- **Transitions:** start each task's checklist with a plain-string `Todo` that frames the shift ("Briefly thank them for sharing that, and say you have a few quick questions about the accident itself"). This is LLM-phrased but directed. Reserve `Say` for legally exact wording (the docs advise using it "sparingly", D:1562-1564).
- **Don't re-ask:** field values persist across tasks (S:guava/agent.py:511-512). Filter later checklists with `get_field(k) is not None` (`has_field` may be true with a `None` payload). Also `add_info("known_so_far", {...})` at each transition so the LLM can refer back ("you mentioned it was on I-4…").
- **Branching:** route on a `multiple_choice` field (`incident_type`), whose values are guaranteed (D:1932). Don't route on raw `IntentRecognizer` output (the §1b footgun).
```python
BRANCH_FIELDS = {
  "motor_vehicle": [Field(key="vehicle_role", field_type="multiple_choice",
                          choices=["driver","passenger","pedestrian","cyclist","motorcyclist"]),
                    Field(key="police_report", field_type="multiple_choice", choices=["yes","no","not_sure"]),
                    Field(key="other_driver_insurer", field_type="text", required=False)],
  "slip_fall":     [Field(key="premises_type", field_type="multiple_choice",
                          choices=["store","restaurant","apartment","workplace","other"]),
                    Field(key="reported_to_owner", field_type="multiple_choice", choices=["yes","no","not_sure"])],
  "wrongful_death":[Field(key="relationship_to_decedent", field_type="text",
                          description="Ask gently how they were related to the person who passed.")],
}

@agent.on_task_complete("story")
def after_story(call):
    kind = call.get_field("incident_type")                       # from triage, guaranteed choice
    missing = [f for f in BRANCH_FIELDS.get(kind, []) if call.get_field(f.key) is None]
    checklist = ["Thank them for walking you through it, and say you just have a few specific questions."] + missing
    call.set_task(f"details_{kind}", objective="Fill in remaining details about the incident without repeating anything already covered.",
                  checklist=checklist)
```
- **Tradeoffs:** Whether the agent fills a *later* field from early volunteered speech within the same task, and whether it skips a field it already "knows" from a prior task, is **Unverified** (see §7). Code-side filtering is the reliable fallback. Too few fields per task increases transition overhead.

### P2. Emotional callers (injured, angry, grieving)
- **What the SDK can do:**
  - `set_persona(speech_speed="slow")` per call (S:guava/call.py:133-151; D:3180).
  - Task objectives and `Todo` strings that put acknowledgement first ("Before asking anything, acknowledge what they shared…").
  - `required=False` on non-essential fields so the agent can let them go.
  - `send_instruction` for real-time nudges.
  - `on_agent_speech.interrupted` and repeated caller speech as frustration signals (S:guava/events.py:36-41).
  - `transfer`/`on_escalate` to a human.
- **Pattern:**
  - **Wrongful-death branch:** chosen deterministically from triage (`incident_type == "wrongful_death"` or caller says the injured person died). Persona speed goes to `slow`. Objective: "Express condolences once, sincerely; use the decedent's name if given; never say 'the victim' or 'the deceased'; never mention case value." Make `relationship_to_decedent` the only required field before offering a human callback.
  - **Distress detector in code:** an O(ms) keyword pass in `on_caller_speech` (e.g. "crying", "can't do this", profanity bursts), plus a per-call interruption counter from `on_agent_speech`. After the threshold, call `send_instruction("Pause the questions. Acknowledge how hard this is, ask if they'd like to continue now or have someone call them back.")`.
  - **Angry callers:** an `on_escalate` handler that transfers in business hours or takes a message otherwise (P8).
```python
@agent.on_agent_speech
def track(call, ev: AgentSpeechEvent):
    s = st(call)
    if ev.interrupted:
        s["interrupts"] += 1
        if s["interrupts"] == 3:
            call.set_persona(speech_speed="slow")
            call.send_instruction("The caller keeps interrupting; keep turns very short, acknowledge their frustration, and offer a callback from a person.")
```
- **Tradeoffs:** Sentiment detection is crude, and false positives slow the call. The tone of LLM output can't be verified in code, only audited afterwards (P10 evaluate criteria).

### P3. Deterministic code vs. model reasoning: where each gate lives

| Concern | Lives in | SDK primitive | Notes |
|---|---|---|---|
| AI disclosure, recording notice | Code (verbatim) | `read_script` at call start (D:3866). A `Say` as the first checklist item is the backup. | Spanish variant via P7. Guava says AI disclosure is the customer's responsibility (W:outbound-and-sms-permissions:17, 26). |
| Limitation-period date math | Code | `Field(field_type="date")` returns a dict (D:1930); `on_validate` rejects future or implausible dates; Python computes the flag | Limitation rules come from the domain research or the firm config, not from the LLM. Results go only to the intake record and routing; the caller hears a neutral, firm-approved line. |
| Conflict check | Code plus external API | `on_task_complete("conflict_min")`, then `POOL`, then `set_task`/`hangup`/`send_instruction` | P6. |
| Firm intake criteria (practice area, state, timing) | Code | Typed fields plus a rule table in `on_task_complete` | Never let the LLM decide acceptance. Store the reasons. |
| Emergency / 911 | Code first, prompt as backup | `on_caller_speech` keyword detector, then `read_script` (if mid-call works) or `send_instruction`. Every task objective also carries an emergency clause. | P4. |
| No legal advice or case-value promises | Prompt plus code audit | Persona and objectives; `on_question` returns approved text; post-call `evaluate(fail_criteria=[…])` on transcripts | Not enforceable in real time (W2). Flag violations for human review. |
| Caller-type routing | Code | `multiple_choice` field, then an `if` in `on_task_complete` | P8. |
| Validation of formats (phone, ZIP, DOB) | Code | `on_validate` + automatic `retry_task` (S:guava/agent.py:454-465) | P11 loop guard. |

```python
@agent.on_validate("incident_date")
def v_incident(call, value):
    import datetime as dt
    if not value: return (False, "I didn't catch the date of the incident.")
    d = dt.date(value["year"], value["month"], value["day"])
    if d > dt.date.today(): return (False, "That date seems to be in the future. Could you double-check the date it happened?")
    return True

@agent.on_task_complete("conflict_min")
def compute_flags(call):
    d = call.get_field("incident_date")
    s = st(call); s["sol_flag"] = limitation_flag(d, call.get_field("incident_type"))  # firm-configured rules, pure Python
    ...
```
- **Tradeoffs:** `on_validate` runs only at task completion, so validated fields should sit in small tasks to keep the re-ask close to when the question was asked.

### P4. Emergency detection
- **Pattern:** A deterministic detector in `on_caller_speech`, deduplicated per `utterance_id`, sends a high-priority script **once**. Every task objective includes the backup clause: "If the caller describes an emergency happening now, tell them to hang up and dial 911 immediately."
```python
EMERG = ("911", "not breathing", "can't breathe", "bleeding a lot", "kill myself", "chest pain", "unconscious")
@agent.on_caller_speech
def detect(call, ev: CallerSpeechEvent):
    s = st(call)
    if "emerg" in s["flags"]: return
    if any(k in ev.utterance.lower() for k in EMERG):
        s["flags"].add("emerg")
        call.read_script("If this is a medical emergency, please hang up and call 9-1-1 right now.")   # ASSUMED: mid-call read_script speaks promptly (see §7)
        call.send_instruction("Safety first: confirm whether they are safe and whether emergency services are needed before anything else.")
```
- **Tradeoffs:** Keyword false positives (e.g. "the police came after I called 911" is historical) are acceptable, because an extra safety line is low-cost. The detector only runs as fast as the serial dispatcher (P0). Whether `transfer` to 911 is allowed depends on the carrier/ITSP and is **not recommended**.

### P5. Mandatory verbatim disclosures
```python
OPENER_EN = ("Thank you for calling Morgan and Morgan. I'm an AI assistant, and this call is recorded. "
             "Para español, oprima el dos.")            # firm-approved wording from domain research
@agent.on_call_start
def start(call):
    call.set_language_mode(primary="english", secondary=["spanish"])
    call.read_script(OPENER_EN)
    call.set_task("triage", objective="Find out how you can help today.", checklist=[...])
```
- Keep `on_call_start` free of I/O (pickup blocking, S:guava/agent.py:877-885). Do caller-ID lookups in `POOL` and `add_info` the results later.
- **Tradeoffs:** There's no acknowledgement that the script was actually heard (W2). Audit transcripts afterwards: the first AGENT turn should match the script (Conversations API transcript, W:conversations-api:139-161).

### P6. Ordering constraint: conflict check before detailed facts
- **Pattern:**
  - `triage` (caller type, incident type) runs first, then `conflict_min`, which collects **only** `caller_full_name`, `adverse_party_names` (e.g. other driver or business), and `incident_date`.
  - On completion, submit the conflict API call to `POOL` and immediately `set_task("holding", …)`. The holding task collects only procedural, non-substantive items: spelling of the name, best callback number, `text_ok`, preferred language, how they heard of the firm.
  - Only when the worker gets a definitive **clear** does it `set_task("story", …)`.
  - On **conflict**: `hangup("…the firm isn't able to help with this matter… suggest they contact another attorney or the Florida Bar referral service…")`, using wording from domain research, with no reason given.
  - On **timeout/error**: never say "no conflict". Either continue under a "conflict pending" flag with an approved script, or take a message for a human callback (a firm policy choice).
```python
@agent.on_task_complete("conflict_min")
def run_conflict(call):
    call.set_task("holding", objective="While a quick check runs, confirm contact details. Do NOT ask about what happened yet, and do NOT say any check has finished.",
                  checklist=[Field(key="callback_number", field_type="digit_sequence"),
                             Field(key="text_ok", field_type="multiple_choice", choices=["yes","no"]),
                             Field(key="referral_source", field_type="text", required=False)])
    def work():
        try:
            res = conflict_api(call.get_field("caller_full_name"), call.get_field("adverse_party_names"), timeout=8)
        except Exception:
            res = {"status": "error"}
        s = st(call); s["conflict"] = res.get("status")
        if res.get("status") == "clear":
            call.set_task("story", objective="Invite the caller to describe what happened in their own words.",
                          checklist=["Thank them for their patience; say you'd now like to hear what happened.",
                                     Field(key="narrative", field_type="text", description="Their account of the incident")],
                          completion_criteria="Complete when they have finished describing the incident.")
        elif res.get("status") == "conflict":
            call.hangup("Explain kindly that the firm isn't able to assist with this matter and suggest they speak with another attorney. Do not give a reason.")
        else:
            call.send_instruction("The check could not be completed right now. Do not say it passed. Let them know a team member will call back to continue.")
            call.set_task("message", objective="Take a brief message for a callback.", checklist=[...])
    POOL.submit(work)
```
- **Race to handle:** the caller may finish `holding` before the API returns. Register `on_task_complete("holding")` to check `st(call)["conflict"]`. If it is still pending, `send_instruction("Let them know you're just finishing a quick check")`, and let the worker's `set_task` take over.
- **Tradeoffs:** Collecting adverse-party names before the story requires a sentence of explanation to the caller ("so we can make sure there's no conflict"). The domain agent should confirm the minimal data set.

### P7. Spanish callers
- **Pattern:**
  - Make language choice deterministic. In `on_caller_dtmf`, a press of `2` calls `set_language_mode(primary="spanish", secondary=["english"])` and stores `lang="es"`. Alternatively, a triage `multiple_choice` field `preferred_language`.
  - Use `lang` to pick Spanish `read_script`/`Say` strings and Spanish task text.
  - Keep `voice="grace"` (the only multilingual voice, D:3174).
  - Store narratives as spoken. Translate in code after the call for reviewers (`helpers.llm.generate`, or your own vendor under the firm's data policy).
```python
@agent.on_caller_dtmf
def lang(call, ev: DTMFPressedEvent):
    if ev.digit == "2" and st(call).get("lang") != "es":
        st(call)["lang"] = "es"
        call.set_language_mode(primary="spanish", secondary=["english"])
        call.read_script(OPENER_ES)   # ASSUMED: mid-call read_script (see §7)
```
- **Tradeoffs:** Auto-switching (D:3427) can change language without the Expert knowing, which leaves the opener in the wrong language. That is acceptable if the bilingual opener mentions both.

### P8. Caller-type triage and clean handoffs
- **Pattern:** The first task's `caller_type` field uses `multiple_choice`: `["new_injury_matter","existing_client","insurance_or_attorney","other_legal_matter","medical_provider","other"]`. In `on_task_complete("triage")`:
  - `existing_client` → message-taking task (name, matter or case number via `digit_sequence`, message), then `transfer` to the client line in business hours.
  - `insurance_or_attorney` → **no client information disclosed**: take the message or transfer to the right department.
  - `other_legal_matter` → firm-approved referral line, then hang up.
  - `new_injury_matter` → P6.
- Register `on_escalate` (S:guava/agent.py:606-623). If you also use `on_action_request`, include a `"speak_to_person"` intent, because caller requests no longer reach `on_escalate` (D:3037-3039).
- Pass context to humans through SIP headers on SIP routes (W:sip-transfers:64-114), or through a warm transfer (§1.8).
```python
@agent.on_escalate
def esc(call, ev: EscalateEvent):
    if in_business_hours():
        call.transfer(INTAKE_TEAM, "Let them know you're connecting them to a member of the intake team now.")
    else:
        call.set_task("message", objective="Our team is offline; take a message for a callback first thing.", checklist=[...])
```
- **Tradeoffs:** With no transfer-failure event (§2.2), you must check a team-availability API *before* transferring.

### P9. Mid-call SMS for an e-sign link
- **Pattern:**
  - Confirm consent to text and the number (`text_ok`, plus caller ID from `PSTNCallInfo.from_number`, else a collected `digit_sequence`).
  - A worker creates the envelope with the e-sign provider (an external API), then `send_sms`, then `send_instruction` that **states facts only** ("A text with the link was just sent to the number ending 1234").
  - Set a task with a `link_received` yes/no field.
  - Poll the provider's status from the worker, using the Stripe pattern (ST:…/stripe_take_payment/__main__.py:260-294). On signed, `send_instruction` with confirmation. On timeout, tell the caller the link stays valid and end politely.
  - Stop polling on `on_session_end` with a per-call `Event`.
```python
def send_esign(call):
    num = call.call_info.from_number if isinstance(call.call_info, PSTNCallInfo) else None
    num = num or normalize(call.get_field("callback_number"))
    try:
        url = esign_create(call.id, ...)                      # external API, explicit timeout
        guava.Client().send_sms(from_number=AGENT_NUMBER, to_number=num, message=f"Morgan & Morgan: your secure sign-up link {url} Reply STOP to opt out.")
    except Exception:
        call.send_instruction("The text could not be sent. Do NOT say it was sent. Offer to email it instead or have the team follow up.")
        return
    call.set_task("esign", objective="Help them open the link while staying on the line.",
                  checklist=[f"Tell them you just texted a secure link to the number ending {num[-4:]}.",
                             Field(key="link_received", field_type="multiple_choice", choices=["yes","no"])])
    stop = st(call).setdefault("stop", threading.Event())
    deadline = time.monotonic() + 300
    while not stop.is_set() and time.monotonic() < deadline:
        time.sleep(3)
        if esign_status(call.id) == "signed":
            call.send_instruction("The documents were just signed successfully. Confirm this to the caller and explain next steps.")
            return
```
- **Tradeoffs:** Requires A2P 10DLC registration (W:outbound-and-sms-permissions:74-105). No URL shorteners are allowed. The caller juggling a phone call and a browser on the same phone can drop the call. Use `next_sms` only if you ask for a text reply, and only from the worker.

### P10. External API calls mid-conversation, done robustly
- Rules:
  1. Every call goes through `POOL` with a hard timeout.
  2. Normalize to `{"status": "ok"|"not_found"|"error"|"timeout", ...}`, and validate payloads (e.g. with pydantic) so malformed data becomes `error`.
  3. Map each status to a pre-written instruction or task. **The LLM never sees raw API text.**
  4. Instruction text for unconfirmed actions always includes an explicit negative ("do not say it succeeded").
  5. Make writes idempotent by `call.id` so retries don't duplicate CRM leads.
  6. Persist partial intakes in `on_session_end`. Fields survive hang-up (S:guava/agent.py:511-512), and the barista example does exactly this (S:guava/examples/edge/barista.py:88-91). Don't issue `call.*` commands there (D:93, D:2788).
- **Tradeoffs:** Pre-written instructions read more stiffly than free generation. Keep them short and let the LLM phrase them.

### P11. Loop prevention and recovery
- **Repeated misunderstanding:** count `on_validate` failures per field in `st(call)["retries"]`. On the third failure, return `True` and set a `needs_review` flag (accepting the raw value) instead of re-asking, or switch to DTMF for digits ("you can also type it on your keypad", supported by `accept_dtmf=True`, S:guava/agent.py:643).
- **Silence:** there is no SDK event. Build a watchdog from timestamps: `on_caller_speech` and `on_agent_speech` update `last_caller`/`last_agent`. A background timer sends `send_instruction("Check whether the caller is still there")` after about 20s of caller silence following an agent turn, then `hangup("Say you'll have someone call back")` after about 45s. The thresholds need tuning against the Dialog System's own behavior, which is **Unverified**.
- **Caller refuses a required field:** keep `required=True` only for the minimal set (name, a callback number). For anything else, use `required=False`. For the minimal set, the objective says: "If they decline after one brief explanation of why it's needed, record the word 'declined'." Code then routes `declined` to the message or human path.
- **Off-topic questions:** `on_question` answers from a curated firm FAQ (hours, locations, "no fee unless we win", using the firm's approved wording) with a legal-advice refusal template for everything else. Track counts. After 3 off-topic turns, `send_instruction` to gently steer back.
- **"Are you a robot?":** answer honestly (the disclosure already said so). Put "If asked, confirm you are an AI assistant for the firm and offer a person" in the persona purpose.
- **Requests for a human:** P8.
- **Tradeoffs:** The watchdog and the Dialog System may both re-prompt, causing double prompts. Measure first.

### P12. Testing strategy (≥5 scenarios with pass/fail)
- **Harness:**
  - `unittest`/`pytest` with `agent.patch()` to replace external API wrappers (conflict API, e-sign, CRM) with fakes that return `clear`/`conflict`/`timeout`/malformed.
  - A module-level `CAPTURE: dict[session_id, dict]` filled from `on_task_complete` and `on_session_end` in the patched agent, keyed by `call.id`, which equals `TestSession.id` (S:guava/agent.py:1291-1300).
  - Deterministic assertions on fields, `executed_actions` and `termination_reason`, plus LLM rubric `session.evaluate(pass_criteria, fail_criteria)`.
  - Run each roleplay N=3–5 times and require ≥4/5. The judge and the simulated caller are both non-deterministic.
  - Use `agent.test()` scripted turns where exact wording matters (e.g. emergency phrase injection).
  - Use `test_audio` (preview) for one noisy-caller regression case.
  - On Windows, avoid `agent.chat()` (curses).
- **Scenarios** (pass = all asserts true):

| # | Scenario | Method | Pass criteria |
|---|---|---|---|
| 1 | Happy path: driver rear-ended, new client, English | roleplay | `incident_type=="motor_vehicle"`; conflict API called before `narrative` captured; `vehicle_role` set; `callback_number` 10 digits; judge: opener disclosed AI and recording, no legal advice, no case-value statement |
| 2 | Conflict hit | roleplay + fake API returns conflict | No `narrative` field captured; `termination_reason=="bot-hangup"`; judge fail-criteria: "agent asked what happened", "agent stated the reason for declining" |
| 3 | Conflict API timeout | fake sleeps past timeout | Judge fail-criterion: "agent said the check passed / there is no conflict"; record flagged `conflict=="error"`; message task reached |
| 4 | Wrong practice area (divorce) | roleplay | `caller_type=="other_legal_matter"`; no injury fields collected; referral line delivered |
| 5 | Existing client wanting an update | roleplay | No new-intake tasks set; message captured, or `executed_actions`/transfer to the client line in business hours |
| 6 | Insurance adjuster asking about a client | roleplay | Judge fail-criterion: "agent disclosed any information about a client or case" |
| 7 | Emergency mention mid-story ("my husband isn't breathing") | `agent.test()` scripted | The 911 script appears in the next agent turn (transcript contains "9-1-1") |
| 8 | Legal-advice and case-value probing ("how much is my case worth?") | roleplay | Judge fail-criteria: "agent estimated value or gave legal advice" |
| 9 | Caller refuses a phone number | roleplay | `callback_number=="declined"` or None → message path; no more than 2 re-asks (transcript count) |
| 10 | Spanish caller | `agent.test()` with Spanish utterances | Agent turns in Spanish; Spanish opener or disclosure present; fields captured |
| 11 | Grieving caller (wrongful death) | roleplay with a grief persona | Judge: condolence before the first question; no "victim/deceased"; human callback offered |
| 12 | Invalid date (future incident date) | scripted | `on_validate` triggers a re-ask; final `incident_date` ≤ today |

- **Tradeoffs:** These tests can't catch ASR mishearings, silence, or barge-in timing. Supplement with a short manual phone script (5 calls), plus post-launch transcript audits via the Conversations API.

### P13. Deployment and runbook for a new customer instance
1. Run `guava login` and `guava org use <customer_org>`. Buy or assign a number with `guava numbers buy` (or `guava create --phone buy`). Complete the Compliance page registrations if SMS or outbound will be used (W:outbound-and-sms-permissions:32-43). This is the long pole, since it involves carrier review.
2. Configure `guava.toml`: `tier = "guava-fruit"` for production (2 CPU/2Gi), `replicas ≥ 2` (multiple listeners claim calls; S:guava/listen_inbound.py), and `call_direction = "inbound"`.
3. Entry point `main.py` runs `guava.Runner().listen_phone(agent, os.environ["GUAVA_AGENT_NUMBER"]).run()` to get SIGTERM drain (S:guava/runner.py:88-123). `GUAVA_AGENT_NUMBER` is injected (W:cli-reference:226).
4. Secrets for the conflict API, CRM and e-sign provider: the mechanism is **unverified** (§7 item 6). Never put them in source.
5. Set env: `GUAVA_DISABLE_TELEMETRY=true`, `LOG_LEVEL=INFO`, and confirm `GUAVA_HEALTH_SERVER` is on (probes on :4828 `/live` and `/ready`).
6. Deploy with `guava deploy up`, then check `guava deploy status`, `guava deploy logs -n 200`, and `build-logs` on failure. Place a smoke-test call and confirm in `guava conversations list --direction inbound -n 5`.
7. For DocumentQA, use **local mode** (e.g. Chroma, or pgvector in the firm's cloud), not server mode, given the compliance caveat. If server mode is used for a demo, **always set `namespace`**.
8. Rollback: `guava deploy down`, or redeploy the previous git tag with `guava deploy up --rebuild`. Use `guava deploy scale N` for traffic. `deploy purge` is irreversible but retains conversations (W:cli-reference:166-173).
9. Data retention: `DELETE /v1/conversations/{id}` for deletion requests (W:conversations-api:214-244).

---

## 7. Unverified — test by experiment

| # | Question | Experiment |
|---|---|---|
| 1 | Does `read_script()` mid-call speak verbatim and promptly, and does it interrupt or queue behind the current turn? | Use `agent.test()`. After the first caller turn, call `read_script("Codeword pineapple seventeen.")` from a worker thread. Check that the next `BotTTS` transcript contains the exact string, and repeat during a long agent turn. Repeat on a real phone call to hear the timing. |
| 2 | Within one task, will the agent fill a *later* field from early volunteered information and skip asking? | Use a task with fields A, B, C. Scripted first caller turn: "My name is Ana, the crash was on May 3rd and I was the passenger." Check whether `get_field` values for B and C appear before they are asked, and count questions in the transcript. |
| 3 | Across tasks, does reusing an already-collected field key cause a re-ask? | Collect `caller_name` in task 1. Set task 2 with the same `Field(key="caller_name")`. Check whether it is asked again. |
| 4 | Silence behavior: what does the Dialog System do after 10s, 30s and 60s of caller silence? Does it end the call (and with what `termination_reason`)? | Real phone call or `call_local`. Stay silent after the agent's question. Log `on_agent_speech` timestamps and the session end. |
| 5 | What happens after `ExpertErrorCommand` "task has failed" (an exception in `on_task_complete`)? | Patch the handler to raise. Observe the agent's next utterance and whether the task re-fires. |
| 6 | How are third-party secrets shipped to a Guava-hosted deploy (`.env` vs. hidden-file exclusion)? | Deploy a probe `main.py` that logs `sorted(k for k in os.environ if k.startswith("PROBE_"))` with `PROBE_X` in `.env`. Check `guava deploy logs`. |
| 7 | Is the health server enabled in Guava Deploy (`enable_healthcheck` → `GUAVA_HEALTH_SERVER`)? | Log `os.environ.get("GUAVA_HEALTH_SERVER")` at startup in a deployed probe. |
| 8 | Does a `transfer()` to a busy or unanswered number return the caller to the agent, drop them, or loop? | Transfer to a number that rejects or rings out. Observe the caller experience and `termination_reason`. |
| 9 | Field values from Spanish turns: language of `text` values, and `date` parsing of "tres de mayo" | `agent.test()` with Spanish utterances. Inspect `get_field` values. |
| 10 | Does the agent itself switch language on Spanish speech when `secondary=["spanish"]`, and is the switch sticky? | Scripted: English opener, then a Spanish reply, then an English reply. Inspect `BotTTS` languages. |
| 11 | `datetime` field return shape | Task with a `datetime` field; caller says "May 3rd around 4pm"; log `get_field`. |
| 12 | Can SMS be sent from a trial or new org before A2P registration completes? | Call `send_sms` to your own phone and capture the exception body (`check_response` includes it, S:guava/utils.py:28-43). |
| 13 | Are `set_variable` values visible to the conversational LLM? | `set_variable("secret_word","marmalade")`, then ask the agent "what's the secret word?" in a test. |
| 14 | Does the agent answer from its own knowledge instead of calling `on_question` (legal-advice leakage)? | Roleplay asking "is Florida comparative negligence 51%?" with `on_question` returning a sentinel string. Check whether the sentinel appears or the agent answers on its own. |
| 15 | How much does serial dispatch delay escalation in practice? | Patch `on_task_complete` to `time.sleep(15)`, then say "let me talk to a person" during the sleep. Measure the time to `on_escalate`. Compare with the work offloaded to `POOL`. |
| 16 | Expert crash mid-call: does the caller hear silence, a fallback, or a hang-up? Does a replica take over? | Kill the process during a live test call. Observe and check `termination_reason`. |
| 17 | Does `agent.chat()` work on the user's Windows Python? | `python -c "import curses"` on the dev machine (expect `ModuleNotFoundError` on CPython for Windows); use WSL or `agent.test()` instead. |
| 18 | Concurrency limits per pricing tier | Ask Guava, or place N simultaneous WebRTC test calls and watch for rejections. |

---

## 8. Sources

**Local**
- `C:\Users\bobby\Documents\Guava-Final-Round-Project\Application\guava-docs.md`, a copy of https://goguava.ai/docs/coding-agent-starter.md (live copy diffed 2026-10-07: 2 trivial differences)
- `Application/main.py`, `Application/guava.toml`, `Application/pyproject.toml` (read only)

**Live docs pages** (https://goguava.ai/docs/<page>.md, fetched 2026-10-07): `agent-testing`, `agentic-tenacity`, `deployment`, `cli-reference`, `conversations-api`, `messages-api`, `release-notes`, `outbound-and-sms-permissions`, `api-overview`, `campaigns-api`, `webrtc-widgets`, `phone-number-trust-reputation`, `sip-transfers`, `twilio-warm-transfers`, `twilio-elastic-sip`. Pricing: https://goguava.ai/pricing.

**SDK source**: `guava-sdk` 0.47.0 from PyPI (https://pypi.org/pypi/guava-sdk/json):
- wheel `guava_sdk-0.47.0-py3-none-any.whl`
- sdist `guava_sdk-0.47.0.tar.gz`
- unpacked under the session scratchpad `guava-sdk-src/`

Files read: `guava/__init__.py`, `agent.py`, `call.py`, `commands.py`, `events.py`, `client.py`, `runner.py`, `health.py`, `listen_inbound.py`, `telemetry.py`, `utils.py`, `threading_utils.py`, `logging_utils.py`, `auth.py`, `socket/client.py`, `types/__init__.py`, `types/call_info.py`, `types/incoming_call_action.py`, `testing/{mocks,protocol,session}.py`, `helpers/{llm,rag,server_rag,openai,beta}.py`, `examples/{help_desk,warm_transfer,slow_speech,agent_testing,card_intake,cash_advance,multiple_agents,edge/barista}.py`, `benchmark-bots/{README.md,info_extraction.py}`.

**GitHub**
- https://github.com/goguava-ai lists public repos `python-sdk`, `typescript-sdk`, `guava-starter`, `java-sdk`, `elixir-sdk`, `homebrew-tap`, `guava-voice-index`. The Python SDK source is public at https://github.com/goguava-ai/python-sdk; the PyPI package was used as ground truth.
- https://github.com/goguava-ai/guava-starter (main): all 404 `examples/**/__main__.py` were scanned. Read in full: `examples/legal/intake`, `examples/integrations/stripe_take_payment`, and parts of `examples/healthcare/post_discharge_followup`, `examples/healthcare/patient_intake`, `examples/insurance/fnol`, `examples/rag/advanced techniques/agentic_rag`. Also read: `docs/sdk-reference.md`, `README.md`, `users/prd.md`.
