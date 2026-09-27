import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
import shutil
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def _worker(code: str) -> list[str]:
    return [PYTHON, "-c", code]


def _report(status="COMPLETED_WITH_EVIDENCE", evidence=None):
    value = {
        "status": status,
        "summary": "fixture worker",
        "changed_files": ["out.txt"],
        "evidence": ["fixture evidence"] if evidence is None else evidence,
    }
    return (
        "import json,os,pathlib;"
        "p=pathlib.Path(os.environ['DEVCONTROL_RESULT_PATH']);"
        f"p.write_text(json.dumps({value!r}),encoding='utf-8')"
    )


class DevcontrolCliTests(unittest.TestCase):
    def setUp(self):
        scratch_root = ROOT / "tmp"
        scratch_root.mkdir(exist_ok=True)
        self.base = scratch_root / ("devcontrol-" + uuid.uuid4().hex)
        self.base.mkdir()
        self.workspace = self.base / "workspace"
        self.workspace.mkdir()

    def tearDown(self):
        shutil.rmtree(self.base)

    def contract(self, **changes):
        raw = {
            "id": "fixture",
            "objective": "write the fixture output",
            "workspace": str(self.workspace),
            "allowed_paths": ["out.txt"],
            "verification_commands": [],
            "deadline_seconds": 10,
        }
        raw.update(changes)
        path = self.base / f"contract-{time.time_ns()}.json"
        path.write_text(json.dumps(raw), encoding="utf-8")
        return path

    def command(self, contract, worker):
        return [
            PYTHON, "-m", "devcontrol", "run", "--contract", str(contract),
            "--worker-command", json.dumps(worker),
        ]

    def run_cli(self, contract, worker, timeout=15):
        return subprocess.run(
            self.command(contract, worker), cwd=ROOT, text=True,
            capture_output=True, timeout=timeout,
        )

    def latest_run(self):
        return max((self.workspace / ".devcontrol" / "runs").iterdir(), key=lambda p: p.stat().st_mtime_ns)

    def state(self):
        return json.loads((self.latest_run() / "state.json").read_text(encoding="utf-8"))

    def test_success_requires_valid_report_scope_and_verification(self):
        worker = _worker("import pathlib; pathlib.Path('out.txt').write_text('ok');" + _report())
        completed = self.run_cli(self.contract(verification_commands=[_worker("import os,sys; assert os.environ['DEVCONTROL_RUN_DIR']; assert os.environ['DEVCONTROL_WORKSPACE']; sys.exit(0)")]), worker)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(self.state()["status"], "COMPLETED")
        manifest = json.loads((self.latest_run() / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["changed_paths"], ["out.txt"])

    def test_worker_false_success_fails_when_verification_fails(self):
        worker = _worker("import pathlib; pathlib.Path('out.txt').write_text('bad');" + _report())
        completed = self.run_cli(self.contract(verification_commands=[_worker("import sys;sys.exit(7)")]), worker)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(self.state()["status"], "FAILED")

    def test_claimed_success_without_any_check_is_rejected(self):
        worker = _worker("import pathlib;pathlib.Path('out.txt').write_text('ok');" + _report())
        completed = self.run_cli(self.contract(), worker)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(self.state()["status"], "FAILED")

    def test_verifier_writes_outside_scope_is_rejected(self):
        worker = _worker("import pathlib;pathlib.Path('out.txt').write_text('ok');" + _report())
        verifier = _worker("import pathlib;pathlib.Path('outside.txt').write_text('no')")
        completed = self.run_cli(self.contract(verification_commands=[verifier]), worker)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("outside.txt", self.state()["details"])

    def test_verification_deadline_stops_owned_process(self):
        worker = _worker("import pathlib;pathlib.Path('out.txt').write_text('ok');" + _report())
        completed = self.run_cli(self.contract(deadline_seconds=1,
            verification_commands=[_worker("import time;time.sleep(30)")]), worker, timeout=8)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(self.state()["status"], "TIMED_OUT")

    def test_windows_liveness_check_preserves_process(self):
        from devcontrol.controller import process_alive
        process = subprocess.Popen(_worker("import time;time.sleep(2)"))
        try:
            self.assertTrue(process_alive(process.pid))
            time.sleep(.3)  # termination on Windows is asynchronous; an immediate poll can miss it
            self.assertIsNone(process.poll())
        finally:
            process.terminate()
            process.wait(timeout=3)

    def test_deadline_covers_worker(self):
        completed = self.run_cli(self.contract(deadline_seconds=1), _worker("import time;time.sleep(30)"), timeout=8)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(self.state()["status"], "TIMED_OUT")

    def test_stop_terminates_owned_worker(self):
        process = subprocess.Popen(
            self.command(self.contract(deadline_seconds=30), _worker("import time;time.sleep(30)")),
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        deadline = time.monotonic() + 5
        run = None
        while time.monotonic() < deadline:
            runs = list((self.workspace / ".devcontrol" / "runs").glob("*")) if (self.workspace / ".devcontrol" / "runs").exists() else []
            if runs and (runs[0] / "state.json").exists():
                run = runs[0]
                break
            time.sleep(.05)
        self.assertIsNotNone(run)
        stopped = subprocess.run([PYTHON, "-m", "devcontrol", "stop", "--run", str(run)], cwd=ROOT, text=True, capture_output=True, timeout=5)
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        process.communicate(timeout=6)
        state = json.loads((run / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["status"], "STOPPED")

    def test_stop_terminates_owned_verification(self):
        worker = _worker("import pathlib;pathlib.Path('out.txt').write_text('ok');" + _report())
        contract = self.contract(deadline_seconds=30, verification_commands=[_worker("import time;time.sleep(30)")])
        process = subprocess.Popen(self.command(contract, worker), cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        deadline = time.monotonic() + 8
        run = None
        while time.monotonic() < deadline:
            runs = list((self.workspace / ".devcontrol" / "runs").glob("*")) if (self.workspace / ".devcontrol" / "runs").exists() else []
            try:
                if runs and json.loads((runs[0] / "state.json").read_text(encoding="utf-8"))["status"] == "VERIFYING":
                    run = runs[0]
                    break
            except (OSError, ValueError):
                pass
            time.sleep(.05)
        self.assertIsNotNone(run)
        stopped = subprocess.run([PYTHON, "-m", "devcontrol", "stop", "--run", str(run)], cwd=ROOT, capture_output=True, timeout=5)
        self.assertEqual(stopped.returncode, 0)
        process.communicate(timeout=6)
        self.assertEqual(json.loads((run / "state.json").read_text(encoding="utf-8"))["status"], "STOPPED")

    def test_scope_violation_fails_completion(self):
        worker = _worker("import pathlib;pathlib.Path('outside.txt').write_text('no');" + _report())
        completed = self.run_cli(self.contract(), worker)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(self.state()["status"], "FAILED")
        self.assertIn("outside.txt", self.state()["details"])

    def test_malformed_report_fails_closed(self):
        worker = _worker("import os,pathlib;pathlib.Path(os.environ['DEVCONTROL_RESULT_PATH']).write_text('{}')")
        completed = self.run_cli(self.contract(), worker)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(self.state()["status"], "FAILED")

    def test_workspace_lock_rejects_concurrent_writer(self):
        first = subprocess.Popen(
            self.command(self.contract(id="first", deadline_seconds=30), _worker("import time;time.sleep(30)")),
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not (self.workspace / ".devcontrol" / "writer.lock").exists():
            time.sleep(.05)
        second = self.run_cli(self.contract(id="second"), _worker(_report()), timeout=5)
        self.assertNotEqual(second.returncode, 0)
        self.assertIn("active writer", second.stderr.lower())
        run = min((self.workspace / ".devcontrol" / "runs").iterdir(), key=lambda p: p.stat().st_mtime_ns)
        subprocess.run([PYTHON, "-m", "devcontrol", "stop", "--run", str(run)], cwd=ROOT, capture_output=True, timeout=5)
        first.communicate(timeout=6)


if __name__ == "__main__":
    unittest.main()
