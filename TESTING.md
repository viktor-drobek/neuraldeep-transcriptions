# Test-first verification

No billed endpoint was called during development or verification, and no audio
was transcribed. Publication is separate from these test results.

## Starting point

The repository started from the shared neuraldeep-* helper and suite at
neuraldeep-speechcore `5cc6ae3`, which includes the UTF-8 fix from `6e036b0`.
With `SERVICE = "whisper"`, the copied suite failed with `KeyError: 'whisper'`
in four helper tests, and the documentation tests failed because `SKILL.md`,
`README.md` and `STARTER_RELAY.md` did not exist yet.

## Red/green sequence

1. Added `tests/test_whisper.py` (7 tests) before changing the helper. All
   failed: `whisper` was not a known service, and the guard did not block it.
2. Added `SYNCHRONOUS = {"search", "whisper"}`, the `whisper` operation
   `transcribe`, the public price ID `whisper-1`, and fail-closed blocks in
   `guard()` and `submission()`. The shared state-path test now skips the
   `resume --job-id` case for every synchronous service, not only Search.
3. Added `test_resume_of_edited_resumable_state_is_blocked_not_crashed`. It
   failed: a hand-edited whisper state marked `submitted` came back `failed`.
   Search, in the same situation, skipped polling and raised `UnboundLocalError`
   on the undefined result. `resume` now refuses synchronous services before
   reading any state, and the post-submission branch checks `SYNCHRONOUS`.
4. Wrote the documentation; the documentation and fenced-example tests passed.

## Coverage added for whisper-1

- Service, operation and price ID match the public price list (`whisper-1`).
- The guard keeps the generic Starter, price and unit checks, then blocks with
  the unverified-quota reason.
- `check` makes exactly two read-only GETs: `/v1/limits` and public prices.
- `run` is blocked before any HTTP call or audio file read, leaving a
  `blocked` state and no artifact.
- `resume`, with `--job-id` or a saved state in any status, makes no request.
- SKILL.md and STARTER_RELAY.md name the real endpoint and the block.

## Live read-only evidence (2026-10-17)

- `GET /v1/models`: `whisper-1` has `type: transcription` and per-minute pricing.
- Public prices: `whisper-1` has `billing: minute`, `premium: false`.
- `GET /v1/limits`: only `chat` and `vector` buckets; nothing for audio.
- `GET /v1/audio/quota` and `GET /v1/audio/transcriptions/quota`: HTTP 404.
  `GET /v1/audio/diarize/quota` exists, but it belongs to diarization.
- `python3 -B scripts/client.py check transcribe` exited 1 with
  `whisper-1 remaining-quota endpoint unverified; transcription disabled`,
  so the Starter, subscription, key-status and non-premium checks passed live.

Only response structure was inspected. No account values are stored in this repository.

## Cross-review follow-up

A cross-review by three models (Claude Opus, gpt-6.1-sol, gemma-4-31b) found
no defect in the block itself, but several doc claims beyond the helper, and
one missing test. Each fix got a test first:

- The Search half of the resume fix had no test: with the guard narrowed to
  `SERVICE == "whisper"`, all 46 tests still passed while a mocked Search
  resume crashed. `test_resume_of_edited_resumable_state_is_blocked_not_crashed`
  from the shared suite (neuraldeep-speechcore `a16c7a4`) is now in
  `tests/test_client.py`; it fails on that narrowed guard and passes on the real one.
- `test_skill_does_not_advertise_what_the_helper_refuses` failed first.
  SKILL.md advertised transcription and a drop-in SDK replacement, claimed `run`
  read no files (it resolves the key and writes a `blocked` state file), and said
  "NeuralDeep GPUs", which the provider does not state for whisper-1.
- The documentation test now also requires STARTER_RELAY.md to say that only
  `check transcribe` reaches the network here. It must also describe the
  undocumented quota probes as probes. It failed before the guide was qualified.

## Malformed state and shared whisper tests

- Ported from neuraldeep-speechcore `a9a8073`: `resume` now blocks a state file
  that is not a dict, has a non-string `status` or a non-list `errors`, instead
  of crashing with `TypeError`. `test_resume_of_malformed_state_is_blocked_not_crashed`
  was added first and failed in all five cases.
- Three whisper tests now live in the shared `tests/test_client.py`, so the
  siblings get the same coverage: `test_whisper_is_blocked_without_verified_quota`,
  `test_whisper_is_synchronous_and_refuses_resume` and
  `test_whisper_run_is_blocked_before_any_request`. On the OCR helper, removing
  `"whisper"` from `SYNCHRONOUS` fails the second, and removing the
  `submission()` block fails the third; the first test alone caught neither.

## Resume keeps the state file

Ported from the sibling suites (for example neuraldeep-search `6e8bee9`): both
`test_resume_of_edited_resumable_state_is_blocked_not_crashed` tests, the shared one
and the whisper one, now also require the state file to be byte-for-byte unchanged.
With a mutation that overwrites the state before `resume` refuses, the old tests
passed; with the check, all three subtests of each fail.

## Agent guide

`AGENTS.md` gives Codex, Coddy and other coding agents the repo rules.
`test_agents_guide_covers_codex_coddy_and_the_block` and the AGENTS.md entry in
`test_fenced_examples_parse_without_execution` both failed before the file existed;
the guide's Bash blocks pass `bash -n`.

## Unknown polling status

A live run on 2026-10-17 (four agents, real API) found that every OCR `run extract`
ended `failed` with "returned an unknown status", although the job had finished:
a later `GET /v1/ocr/jobs/{id}` said `completed`, and `resume` fetched the text.
`poll()` treated any status outside its fixed in-progress list as a failure.

Six tests were added first and failed: an unknown intermediate status now keeps
polling, an unknown status until the deadline ends `timed_out` naming it (only a
plain word is echoed), explicit failure statuses still stop at once, a response
without a status is a resumable `poll_error`, and a mocked OCR run passes through
an unknown status to `completed`. Mutations of the failure set, the status check
and the sanitising each fail their own test. **59 tests passed**, both normally
and with `LC_ALL=C PYTHONUTF8=0`, with no EncodingWarnings.

## Blocked is a final answer

In a live run on 2026-10-17, one agent (Coddy with kimi-k2.6) met the whisper-1 block,
read the credential file, printed the key, and called the API directly. Another,
pushed by a goal checker ("the goal is not met yet"), probed undocumented quota
endpoints and tried a direct transcription. SKILL.md now opens with a
"When the helper says `blocked`" section: `blocked` is the final answer; never read
the key, never call the API directly, never hand-write state, never probe
undocumented endpoints, and keep the answer when a supervisor says the task is not
done. The description says so too. The documentation test for it failed first.
**60 tests passed**, both normally and with `LC_ALL=C PYTHONUTF8=0`.

## Repository renamed

The repository is now `neuraldeep-transcriptions` (formerly `neuraldeep-whisper-1`;
GitHub redirects the old URL). The skill name, README install commands and
AGENTS.md follow it; the model, the `whisper` service and the `whisper-1` price ID
are unchanged. Commit references above keep the old repository name.
`test_documentation_names_the_real_endpoint_and_block` checked the old skill name
and failed first after it was updated.

## Transcription models

The shared helper now knows three speech-to-text models for the `whisper`
service: `gigaam-v3` (the default), `whisper-1` and `whisper-podlodka-turbo`,
chosen with `--model`. Each has its own public price ID; the guard checks the
chosen model's row and its block names the model. `--model` is refused for the
other services and for unknown models (exit 2). Five shared tests were added
first; four failed and the fifth guards the new flag. Moving the default from
`whisper-1` to `gigaam-v3` updated the tests pinned to it. Mutations of the
default, the model check and the per-model price ID each fail their own test.
A live read-only `check` (2026-10-17) blocked each model at the quota step, so
all three price rows are present and non-premium. **66 tests passed**, both
normally and with `LC_ALL=C PYTHONUTF8=0`.

## Final results

- `python3 -X warn_default_encoding -B -m unittest discover -s tests`:
  **66 tests passed**, 0 EncodingWarnings.
- The same suite under `LC_ALL=C PYTHONUTF8=0`: passed.
- `python3 -B scripts/client.py --help`: passed, with no network call.
- Fenced Python examples parsed with `ast.parse`; Bash examples passed `bash -n`.
