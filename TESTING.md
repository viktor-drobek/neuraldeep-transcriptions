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

## Agent rule surfaces

Added `tests/test_agent_rules.py` (10 tests) before any rule file existed; all
10 failed because `.codex/hooks/attach_rules.py`, the rules and `CLAUDE.md` were
missing. Then added Cursor rules (`.cursor/rules/*.mdc`), their Claude Code
mirrors with identical bodies (`.claude/rules/*.md`), the Codex hook that attaches
the Cursor rules (`.codex/hooks.json`, `.codex/hooks/attach_rules.py`),
`CLAUDE.md` as a symlink to `AGENTS.md`, and the Delivery workflow and Rules Sync
sections in `AGENTS.md`. The tests check the pairing and scope mapping, that
every glob matches a file, and the hook itself: always-on rules at session start,
the client rule once per session for patch add, update, delete and rename and for
`Edit` and `Write`, and fail-open on bad input. Eight mutations (a widened or
narrowed scope, `paths` differing from `globs`, body drift, a missing mirror, a
dead glob, `.codex/rules.md`, a copied `CLAUDE.md`) each failed a test. The test
file and `.codex/hooks/` are identical across the neuraldeep-* repositories.
**76 tests passed**, both normally and with `LC_ALL=C PYTHONUTF8=0`, with no
`EncodingWarning` under `-X warn_default_encoding`.

## Release metadata (v1.0.0)

Added `tests/test_release.py` (3 tests, identical across the neuraldeep-*
repositories) first. Two failed: `SKILL.md` had no `metadata.version` and
`AGENTS.md` had no release steps; the tag check is skipped outside a tag build.
`metadata.version: 1.0.0` is now in the `SKILL.md` frontmatter, the key Coddy
reads (`coddy skills list` showed `1.0.0` for a copy under a scratch
`CODDY_HOME`), and `AGENTS.md` has a Releases section. With
`GITHUB_REF_TYPE=tag`, `GITHUB_REF_NAME=v1.0.0` passed and `v1.0.1` failed.
**79 tests passed** (1 skipped outside a tag build), both normally and with
`LC_ALL=C PYTHONUTF8=0`, with no `EncodingWarning` under
`-X warn_default_encoding`.

## Final results

- `python3 -X warn_default_encoding -B -m unittest discover -s tests`:
  **79 tests passed** (1 skipped outside a tag build), 0 EncodingWarnings.
- The same suite under `LC_ALL=C PYTHONUTF8=0`: passed.
- `python3 -B scripts/client.py --help`: passed, with no network call.
- Fenced Python examples parsed with `ast.parse`; Bash examples passed `bash -n`.

## Diarization service

Port from neuraldeep-diarization: the shared helper now knows the `diarize`
service (`POST /v1/audio/diarize`, price ID `audio:diarize`). Its quota at
`/v1/audio/diarize/quota` reports `used` and `limit` minutes per `day` and
`month`, verified read-only on 2026-10-18, and the guard requires `limit - used`
to cover `--minutes`, at most 240, with files of at most 500 MB. An offline
`merge` command joins a diarization with a timed transcript. `--minutes` and
`merge` are refused for the other services (exit 2), and this service's
behaviour is unchanged. The 16 shared tests and the merge case of the UTF-8 test
were added first and failed with `KeyError: 'diarize'` and the missing
`merge_transcript`. `SKILL.md` now points to the neuraldeep-diarization skill, whose `merge` consumes this endpoint's timed transcripts. `STARTER_RELAY.md` lists the diarization bucket.
**95 tests passed** (1 skipped outside a tag build), both normally and with
`LC_ALL=C PYTHONUTF8=0`, with no `EncodingWarning` under
`-X warn_default_encoding`.

## Diarization formats and cross-review fixes

Port from neuraldeep-diarization. `merge --format json|vtt|srt|rttm` writes
WebVTT with voice tags, SRT with a speaker prefix, or RTTM converted locally
from the diarization alone. A cross-review of the diarization skill led to
shared fixes, each with a test written first:
- the diarization POST waits `max(120, 30 * minutes)` s;
- every service's `run` checks `--output` before any request, so an output
  equal to `--file` or in a missing directory blocks instead of overwriting the
  input or losing a paid answer;
- subtitle speaker labels are flattened, and the 1 ms cue minimum applies after
  rounding;
- `finite()` rejects integers too large for a float;
- `merge` sorts its inputs by time and compares overlaps to the microsecond;
- the 500 MB cap is tested.
`STARTER_RELAY.md` documents the output check, and this service is otherwise
unchanged. The 15 new shared tests failed first, apart from the flag-rule and
cap tests, which only add coverage.
**110 tests passed** (1 skipped outside a tag build), both normally and with
`LC_ALL=C PYTHONUTF8=0`, with no `EncodingWarning` under
`-X warn_default_encoding`.

## Second cross-review fixes

Port from neuraldeep-diarization `e376732`. `run` now also blocks an
`--output` that is a directory, and checks the unresolved parent that
`atomic_write()` uses, so a symlink in a read-only directory blocks too.
WebVTT and SRT get one cue per transcript segment, through `label_segments()`.
Huge timestamps and deeply nested input JSON end `blocked`. `merge` parses
input bytes, accepting a UTF-8 byte order mark, and names a file that is not
valid JSON. The new and changed shared tests failed first, apart from the
read-only and missing directory cases, which already passed.
**115 tests passed** (1 skipped outside a tag build), both normally and with
`LC_ALL=C PYTHONUTF8=0`, with no `EncodingWarning` under
`-X warn_default_encoding`.

## Third cross-review fixes

Port from neuraldeep-diarization `e4bdae5`. `run` requires read, write and
search permission on the output directory, since `atomic_write()` needs all
three. `merge` decodes strict UTF-8 (a byte order mark is fine), so UTF-16,
UTF-32 and surrogate bytes block; a missing input, an unwritable output and a
lone surrogate escape block with their own messages. `--output` equal to
`--diarization` is tested. The new shared tests failed first, apart from that
coverage case. **117 tests passed** (1 skipped outside a tag build), both
normally and with `LC_ALL=C PYTHONUTF8=0`, with no `EncodingWarning` under
`-X warn_default_encoding`.

## Fourth cross-review fixes

Port from neuraldeep-diarization `336ccf4`. The output check uses
`os.path.isdir()`, because `Path.is_dir()` raises `PermissionError` on Python
3.10 to 3.12 and broke the 3.10 CI job; `run` blocks replacing another user's
file in a sticky directory before any request; the RTTM file ID shows
non-UTF-8 file name bytes as U+FFFD; a tie test has the first speaker last in
alphabetical order. The sticky-directory and file-name tests failed first.
**120 tests passed** (1 skipped outside a tag build), both normally and with
`LC_ALL=C PYTHONUTF8=0`, with no `EncodingWarning` under
`-X warn_default_encoding`, and on Python 3.10.22 (Docker `python:3.10-slim`,
non-root, no network).

## Fifth cross-review fixes

Port from neuraldeep-diarization `49688de`. `run` blocks an output name the
file system refuses (any `lstat` error except `FileNotFoundError`), and the
`run` and `merge` same-file checks add `os.path.samefile()` for hard links and
case aliases. `--format rttm` blocks a lone surrogate speaker label with its own
message, and the diarization artifact is written with ASCII escapes. The new
shared tests failed first. **124 tests passed** (1 skipped outside a tag build),
both normally and with `LC_ALL=C PYTHONUTF8=0`, with no `EncodingWarning` under
`-X warn_default_encoding`, and on Python 3.10.22 (Docker `python:3.10-slim`,
non-root, no network).

## Sixth cross-review fixes

Port from neuraldeep-diarization `5916a17`. An output that is the state file
through a case alias blocks once the state exists, before any request; a new
output name is created with `O_EXCL` and removed before the preflight, so names
vfat, exFAT or SMB refuse on create block early; consecutive unassigned merge
segments stay separate turns. The new shared tests failed first.
**127 tests passed** (1 skipped outside a tag build), both normally and with
`LC_ALL=C PYTHONUTF8=0`, with no `EncodingWarning` under
`-X warn_default_encoding`, and on Python 3.10.22 (Docker `python:3.10-slim`,
non-root, no network).

## Seventh cross-review fix

Port from neuraldeep-diarization `c10a179`. Once the state exists, `run`
blocks an input file that is the state file, also through a case alias, before
any request; before, `--file x --state x` with no `x` sent the helper's own
state JSON. The new shared test failed first. **128 tests passed** (1 skipped
outside a tag build), both normally and with `LC_ALL=C PYTHONUTF8=0`, with no
`EncodingWarning` under `-X warn_default_encoding`, and on Python 3.10.22
(Docker `python:3.10-slim`, non-root, no network).
