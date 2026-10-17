import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("client", Path(__file__).parents[1] / "scripts" / "client.py")
client = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(client)


def limits():
    return {"tier": "starter", "key": {"status": "ok", "billing_mode": "subscription"},
            "decision": {"can_request": True}}


def prices(premium=False):
    return {"prices": [{"model": "whisper-1", "billing": "minute", "rub_per_min": 1.0, "premium": premium}]}


def run_cli(argv):
    with patch.object(sys, "argv", ["client.py", *argv]), patch("sys.stdout", new_callable=io.StringIO) as out:
        code = client.main()
    return code, json.loads(out.getvalue())


class WhisperTests(unittest.TestCase):
    def test_repo_service_and_public_price_id(self):
        self.assertEqual(client.SERVICE, "whisper")
        self.assertEqual(client.OPERATIONS["whisper"], ("transcribe",))
        self.assertEqual(client.price_id("whisper", "transcribe"), "whisper-1")
        self.assertIn("whisper", client.SYNCHRONOUS)

    def test_guard_blocks_whisper_without_verified_quota(self):
        with self.assertRaises(client.Blocked) as raised:
            client.guard("whisper", "transcribe", limits(), prices(), {}, 1)
        self.assertIn("whisper-1 remaining-quota endpoint unverified", str(raised.exception))
        # The generic Starter, price and unit checks still run first.
        for lim, price, units in ((dict(limits(), tier="pro"), prices(), 1),
                                  (limits(), prices(premium=True), 1),
                                  (limits(), {"prices": []}, 1),
                                  (limits(), prices(), 0)):
            with self.assertRaises(client.Blocked) as raised:
                client.guard("whisper", "transcribe", lim, price, {}, units)
            self.assertNotIn("unverified", str(raised.exception))

    def test_check_reads_only_limits_and_prices(self):
        with patch.object(client, "resolve_key", return_value="fixture"), \
                patch.object(client, "request", side_effect=[limits(), prices()]) as req:
            code, result = run_cli(["check"])
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["service"], "whisper")
        self.assertIn("unverified", result["errors"][0])
        self.assertEqual([c.args[:2] for c in req.call_args_list],
                         [("GET", client.HUB + "/limits"), ("GET", client.PRICES)])

    def test_run_is_blocked_before_any_request_or_file_read(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(client, "resolve_key", return_value="fixture"), \
                patch.object(client, "request") as req, patch.object(client, "multipart") as body:
            state, output = Path(tmp) / "state.json", Path(tmp) / "transcript.json"
            code, result = run_cli(["run", "transcribe", "--file", str(Path(tmp) / "missing.wav"),
                                    "--state", str(state), "--output", str(output)])
            saved = json.loads(state.read_text(encoding="utf-8"))
            self.assertFalse(output.exists())
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("transcription disabled", result["errors"][0])
        self.assertEqual(saved["status"], "blocked")
        self.assertIsNone(saved["provider_job_id"])
        self.assertEqual(saved["artifacts"], [])
        req.assert_not_called()
        body.assert_not_called()

    def test_resume_job_id_is_refused_for_synchronous_transcription(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(client, "resolve_key", return_value="fixture"), \
                patch.object(client, "request") as req:
            state = Path(tmp) / "state.json"
            code, result = run_cli(["resume", "--job-id", "job-fixture", "--state", str(state),
                                    "--output", str(Path(tmp) / "transcript.json")])
            self.assertFalse(state.exists())
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("Synchronous whisper has no resumable job endpoint", result["errors"][0])
        req.assert_not_called()

    def test_resume_of_blocked_state_makes_no_request(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(client, "resolve_key", return_value="fixture"), \
                patch.object(client, "request") as req:
            state = Path(tmp) / "state.json"
            client.save_state(state, client.state_template("task-fixture", "whisper"))
            code, result = run_cli(["resume", "--state", str(state), "--output", str(Path(tmp) / "transcript.json")])
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "blocked")
        req.assert_not_called()

    def test_resume_of_edited_resumable_state_is_blocked_not_crashed(self):
        for status in ("submitted", "timed_out", "poll_error"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp, \
                    patch.object(client, "resolve_key", return_value="fixture"), patch.object(client, "request") as req:
                state = Path(tmp) / "state.json"
                saved = client.state_template("task-fixture", "whisper")
                saved.update(status=status, provider_job_id="job-fixture")
                client.save_state(state, saved)
                code, result = run_cli(["resume", "--state", str(state), "--output", str(Path(tmp) / "transcript.json")])
                self.assertFalse((Path(tmp) / "transcript.json").exists())
            self.assertEqual(code, 1)
            self.assertEqual(result["status"], "blocked")
            self.assertIn("no resumable job endpoint", result["errors"][0])
            req.assert_not_called()

    def test_documentation_names_the_real_endpoint_and_block(self):
        root = Path(__file__).parents[1]
        skill = (root / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: neuraldeep-whisper-1\n", skill)
        self.assertIn("/v1/audio/transcriptions", skill)
        self.assertIn("python3 scripts/client.py check transcribe", skill)
        relay = (root / "STARTER_RELAY.md").read_text(encoding="utf-8")
        self.assertRegex(relay, r"\| Whisper \| \*\*Unverified: transcription blocked\.\*\*")
        self.assertIn("In this repository only `check transcribe` reaches the network", relay)
        self.assertNotIn("used only documented read-only GETs", relay)

    def test_skill_does_not_advertise_what_the_helper_refuses(self):
        skill = (Path(__file__).parents[1] / "SKILL.md").read_text(encoding="utf-8")
        for claim in ("drop-in", "Short audio transcribed", "short audio transcription",
                      "NeuralDeep GPUs", "before any network call or file read"):
            self.assertNotIn(claim, skill)
        # run still resolves the key and leaves a blocked state file behind.
        self.assertIn("writes a `blocked` state file", skill)


if __name__ == "__main__":
    unittest.main()
