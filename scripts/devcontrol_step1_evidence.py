"""Run the ten step-1 deliberate-failure cases through the real devcontrol CLI.

Workers are small local Python fixtures (no model calls). Prints one markdown row
per case: expected result, observed result, PASS/MISMATCH.
"""
import json
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
REPORT = ("import json,os,pathlib;pathlib.Path(os.environ['DEVCONTROL_RESULT_PATH'])"
          ".write_text(json.dumps({'status':'COMPLETED_WITH_EVIDENCE','summary':'fixture',"
          "'changed_files':['out.txt'],'evidence':['fixture says done']}),encoding='utf-8')")
WRITE_OK = "import pathlib;pathlib.Path('out.txt').write_text('ok');"
CHECK = "import pathlib,sys;sys.exit(0 if pathlib.Path('out.txt').read_text()=='ok' else 3)"


class Case:
    def __init__(self):
        self.base = ROOT / "tmp" / ("step1-" + uuid.uuid4().hex[:8])
        self.ws = self.base / "workspace"
        self.ws.mkdir(parents=True)

    def contract(self, **changes):
        raw = {"id": "case", "objective": "write ok to out.txt", "workspace": str(self.ws),
               "allowed_paths": ["out.txt"], "deadline_seconds": 10,
               "verification_commands": [[PY, "-c", CHECK]]}
        raw.update(changes)
        path = self.ws / f"contract-{time.time_ns()}.json"
        path.write_text(json.dumps(raw), encoding="utf-8")
        return path

    def cmd(self, contract, code):
        return [PY, "-m", "devcontrol", "run", "--contract", str(contract), "--worker-command", json.dumps([PY, "-c", code])]

    def run(self, contract, code, timeout=20):
        return subprocess.run(self.cmd(contract, code), cwd=ROOT, text=True, capture_output=True, timeout=timeout)

    def runs(self):
        folder = self.ws / ".devcontrol" / "runs"
        return sorted(folder.iterdir(), key=lambda p: p.stat().st_mtime_ns) if folder.exists() else []

    def state(self, run=None):
        run = run or self.runs()[-1]
        return json.loads((run / "state.json").read_text(encoding="utf-8"))

    def wait_for_run(self, status="RUNNING", seconds=8):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            runs = self.runs()
            if runs and (runs[0] / "state.json").exists():
                try:
                    if self.state(runs[0]).get("status") == status:
                        return runs[0]
                except (json.JSONDecodeError, OSError):
                    pass
            time.sleep(.05)
        return None

    def stop(self, run):
        subprocess.run([PY, "-m", "devcontrol", "stop", "--run", str(run)], cwd=ROOT, capture_output=True, timeout=10)

    def close(self):
        shutil.rmtree(self.base, ignore_errors=True)


def observed(state):
    return f"{state['status']}: {state.get('details') or ''}".strip().rstrip(":")


def case_1(c):
    c.run(c.contract(), WRITE_OK + REPORT)
    return observed(c.state()), c.state()["status"] == "COMPLETED"


def case_2(c):
    c.run(c.contract(), "import pathlib;pathlib.Path('out.txt').write_text('bad');" + REPORT)
    s = c.state()
    return observed(s), s["status"] == "FAILED"


def case_3(c):
    c.run(c.contract(), WRITE_OK + "pathlib.Path('secret.txt').write_text('x');" + REPORT)
    s = c.state()
    kept = (c.ws / "secret.txt").exists()
    return observed(s) + f"; unauthorized file kept for inspection: {kept}", s["status"] == "FAILED" and "secret.txt" in s["details"] and kept


def case_4(c):
    c.run(c.contract(), "import os,pathlib;pathlib.Path(os.environ['DEVCONTROL_RESULT_PATH']).write_text('not json')")
    s = c.state()
    return observed(s)[:120], s["status"] == "FAILED" and "invalid worker report" in s["details"]


def case_5(c):
    started = time.monotonic()
    c.run(c.contract(deadline_seconds=2), "import time;time.sleep(60)")
    s = c.state()
    return observed(s) + f"; ended after {time.monotonic() - started:.1f}s", s["status"] == "TIMED_OUT"


def case_6(c):
    started = time.monotonic()
    c.run(c.contract(deadline_seconds=3, verification_commands=[[PY, "-c", "import time;time.sleep(60)"]]), WRITE_OK + REPORT)
    s = c.state()
    return observed(s) + f"; ended after {time.monotonic() - started:.1f}s", s["status"] == "TIMED_OUT"


def case_7(c):
    results = []
    for label, contract, code in (
        ("during worker", c.contract(deadline_seconds=60), "import time;time.sleep(60)"),
        ("during verification", c.contract(deadline_seconds=60, verification_commands=[[PY, "-c", "import time;time.sleep(60)"]]), WRITE_OK + REPORT),
    ):
        for run in c.runs():
            shutil.rmtree(run)
        started = time.monotonic()
        process = subprocess.Popen(c.cmd(contract, code), cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        run = c.wait_for_run("RUNNING")
        if label == "during verification":
            end = time.monotonic() + 8
            while run and time.monotonic() < end and not any("verification" in line for line in (run / "events.jsonl").read_text(encoding="utf-8").splitlines()[-1:]) and not (run / "result.json").exists():
                time.sleep(.05)
            time.sleep(.5)
        c.stop(run)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        s = c.state(run)
        logs = (run / "events.jsonl").exists()
        results.append((label, s["status"], time.monotonic() - started, logs))
    text = "; ".join(f"{label}: {status} after {secs:.1f}s, logs kept {logs}" for label, status, secs, logs in results)
    return text, all(status == "STOPPED" and secs < 15 and logs for _, status, secs, logs in results)


def case_8(c):
    first = subprocess.Popen(c.cmd(c.contract(id="first", deadline_seconds=30), "import time;time.sleep(30)"), cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    run = c.wait_for_run("RUNNING")
    second = c.run(c.contract(id="second"), WRITE_OK + REPORT)
    c.stop(run)
    first.wait(timeout=10)
    refused = second.returncode != 0 and "active writer" in second.stderr.lower()
    return f"second task exit {second.returncode}: {second.stderr.strip().splitlines()[-1] if second.stderr.strip() else ''}", refused


def case_9(c):
    check = c.ws / "check.py"
    check.write_text(CHECK.replace(";", "\n"), encoding="utf-8")
    contract = c.contract(verification_commands=[[PY, "check.py"]])
    tamper = "import pathlib;pathlib.Path('out.txt').write_text('bad');pathlib.Path('check.py').write_text('import sys;sys.exit(0)');"
    c.run(contract, tamper + REPORT)
    s1 = c.state()
    c.run(c.contract(), WRITE_OK + f"pathlib.Path(r'{contract.name}').write_text('{{}}');" + REPORT)
    s2 = c.state()
    return f"edits check script -> {observed(s1)}; edits contract -> {observed(s2)}", s1["status"] == "FAILED" and s2["status"] == "FAILED"


def case_10(c):
    sys.path.insert(0, str(ROOT))
    from devcontrol.controller import process_alive
    process = subprocess.Popen([PY, "-c", "import time;time.sleep(5)"])
    try:
        alive = process_alive(process.pid)
        time.sleep(.3)
        still_running = process.poll() is None
    finally:
        process.terminate()
        process.wait(timeout=5)
    return f"reported alive: {alive}; still running after check: {still_running}", alive and still_running


CASES = [
    ("Worker writes the required content in the allowed file", "COMPLETED", case_1),
    ("Worker writes wrong content but reports success", "FAILED by content check", case_2),
    ("Worker writes an unauthorized file", "FAILED by scope check; file preserved", case_3),
    ("Worker gives an invalid result", "FAILED with specific reason", case_4),
    ("Worker sleeps beyond its deadline", "TIMED_OUT", case_5),
    ("Verification command sleeps beyond the deadline", "TIMED_OUT", case_6),
    ("User requests stop during a worker or verification", "STOPPED in both; evidence kept", case_7),
    ("A second managed task tries to write in the same workspace", "Refused", case_8),
    ("Worker changes the task or its verification script", "FAILED in both", case_9),
    ("Windows process liveness is checked", "Process keeps running", case_10),
]


def main():
    rows = []
    for label, expected, function in CASES:
        c = Case()
        try:
            text, ok = function(c)
        except Exception as error:
            text, ok = f"harness error: {error!r}", False
        finally:
            c.close()
        rows.append((label, expected, text.replace("|", "/"), "PASS" if ok else "MISMATCH"))
        print(f"{'PASS' if ok else 'MISMATCH'}: {label}", file=sys.stderr, flush=True)
    print("| Input/action | Expected | Observed | Result |\n|---|---|---|---|")
    for row in rows:
        print("| " + " | ".join(row) + " |")
    return 0 if all(r[3] == "PASS" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
