import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from project_memory.store import Store


class HookTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT / "tmp" / "memory-hooks" / uuid.uuid4().hex
        self.root.mkdir(parents=True)
        self.store = Store(self.root)
        self.store.put(dict(id="step-1", kind="checkpoint", title="Discuss input", summary="Waiting for Lohith", status="review", links=[]), 0, "fixture")
        self.store.put(dict(id="project", kind="project", title="Application builder", summary="JD to application", status="active", focus="step-1", checkpoints=["step-1"], links=[]), 0, "fixture")

    def tearDown(self):
        assert self.root.resolve().is_relative_to((ROOT / "tmp" / "memory-hooks").resolve())
        shutil.rmtree(self.root)

    def hook(self, kind, **fields):
        payload = dict(cwd=str(self.root), hook_event_name=kind, session_id="fixture-only", **fields)
        p = subprocess.run([sys.executable, str(ROOT / "scripts" / "memory_hook.py"), "--root", str(self.root), "--synthetic"],
                           input=json.dumps(payload), capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout or "{}")

    def test_start_loads_current_state_and_does_not_claim_real_hook_activation(self):
        result = self.hook("SessionStart", source="clear")
        self.assertIn("Waiting for Lohith", result["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.store.timeline(1)[0]["origin"], "synthetic")

    def test_tool_events_pair_without_copying_credentials_or_transcripts(self):
        self.hook("PreToolUse", tool_name="Bash", tool_use_id="call-1", tool_input={"command": "echo secret-credential-value"})
        self.hook("PostToolUse", tool_name="Bash", tool_use_id="call-1", tool_response={"exit_code": 1, "output": "secret-credential-value"})
        rows = self.store.timeline(2)
        self.assertNotIn("secret-credential-value", json.dumps(rows))
        self.assertEqual(rows[0]["exit_code"], 1)
        self.assertGreaterEqual(rows[0]["elapsed_ms"], 0)

    def test_stop_records_pause_without_accepting_checkpoint(self):
        log = next((self.store.home / "events").glob("*.jsonl"))
        with log.open("ab") as f:
            f.write(b'{"partial":')
        self.hook("Stop")
        self.assertEqual(self.store.get("step-1")["status"], "review")
        self.assertTrue((self.root / "project-memory" / "cache" / "status.html").exists())


if __name__ == "__main__":
    unittest.main()
