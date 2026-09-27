import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .models import Contract, Event, TERMINAL_STATES, WorkerReport


IGNORED_TOP_LEVEL = {".git", ".devcontrol", ".env", "private", "jobs", "output", "outputs", "cache", "__pycache__"}


def _atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _path_in_scope(path: str, scopes: list[str]) -> bool:
    return any(path == scope or path.startswith(scope + "/") for scope in scopes)


def workspace_hashes(workspace: Path, explicit_paths: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for root, directories, files in os.walk(workspace):
        relative_root = Path(root).relative_to(workspace)
        kept = []
        for directory in directories:
            rel = (relative_root / directory).as_posix()
            if directory in IGNORED_TOP_LEVEL and not _path_in_scope(rel, explicit_paths):
                continue
            kept.append(directory)
        directories[:] = kept
        for name in files:
            rel = (relative_root / name).as_posix()
            top = rel.split("/", 1)[0]
            if top in IGNORED_TOP_LEVEL and not _path_in_scope(rel, explicit_paths):
                continue
            path = workspace / rel
            if path.is_file() and not path.is_symlink():
                result[rel] = _sha256(path)
    return result


def changed_paths(before: dict[str, str], after: dict[str, str]) -> list[str]:
    return sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))


def process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        # os.kill(pid, 0) terminates the process on Windows; query its exit code instead.
        import ctypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.restype = ctypes.c_void_p
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return ctypes.get_last_error() == 5  # access denied: exists but not ours
        try:
            code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(ctypes.c_void_p(handle), ctypes.byref(code)):
                return False
            return code.value == 259  # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(ctypes.c_void_p(handle))
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def kill_tree(pid: int) -> None:
    if not process_alive(pid):
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, check=False)
    else:
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


class WorkspaceLock:
    def __init__(self, workspace: Path, run_dir: Path):
        self.path = workspace / ".devcontrol" / "writer.lock"
        self.owner = {"pid": os.getpid(), "run": str(run_dir)}

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(2):
            try:
                descriptor = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
            except FileExistsError:
                try:
                    current = json.loads(self.path.read_text(encoding="utf-8"))
                    pid = int(current["pid"])
                except (OSError, ValueError, KeyError, json.JSONDecodeError):
                    raise RuntimeError("active writer lock is unreadable; refusing unsafe recovery")
                if process_alive(pid):
                    raise RuntimeError(f"active writer already owns workspace (pid {pid})")
                self.path.unlink()
                continue
            with os.fdopen(descriptor, "w", encoding="utf-8") as target:
                json.dump(self.owner, target)
            return
        raise RuntimeError("could not acquire workspace writer lock")

    def release(self) -> None:
        try:
            if json.loads(self.path.read_text(encoding="utf-8")) == self.owner:
                self.path.unlink()
        except (OSError, json.JSONDecodeError):
            pass


class RunController:
    def __init__(self, contract: Contract, contract_source: Path, worker_command: list[str] | None, codex: str | None):
        self.contract = contract
        self.contract_source = contract_source.resolve()
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        safe_id = "".join(c if c.isalnum() or c in "-_" else "-" for c in contract.id)
        self.run_dir = contract.workspace / ".devcontrol" / "runs" / f"{safe_id}-{stamp}"
        self.worker_command = worker_command
        self.codex = codex
        self.child: subprocess.Popen | None = None
        self.lock = WorkspaceLock(contract.workspace, self.run_dir)
        self.started = time.monotonic()

    def event(self, event: str, status: str, details: str = "") -> None:
        item = Event(timestamp=datetime.now(timezone.utc).isoformat(), run=str(self.run_dir), event=event, status=status, details=details)
        with (self.run_dir / "events.jsonl").open("a", encoding="utf-8") as target:
            target.write(item.model_dump_json() + "\n")
        print(f"[{status}] {event}" + (f": {details}" if details else ""), flush=True)

    def state(self, status: str, details: str = "", **extra) -> None:
        _atomic_json(self.run_dir / "state.json", {"status": status, "details": details, **extra})

    def remaining(self) -> float:
        return self.contract.deadline_seconds - (time.monotonic() - self.started)

    def _implicit_protected(self) -> list[str]:
        protected = list(self.contract.protected_paths)
        for source in (self.contract_source, self.contract.brief_file):
            if source is not None:
                try:
                    rel = source.relative_to(self.contract.workspace).as_posix()
                except ValueError:
                    continue
                if rel not in protected:
                    protected.append(rel)
        package = Path(__file__).resolve().parent
        try:
            rel = package.relative_to(self.contract.workspace).as_posix()
            if not _path_in_scope(rel, self.contract.allowed_paths):
                protected.append(rel)
        except ValueError:
            pass
        for command in self.contract.verification_commands:
            for argument in command:
                candidate = Path(argument)
                candidate = candidate if candidate.is_absolute() else self.contract.workspace / candidate
                if candidate.is_file():
                    try:
                        rel = candidate.resolve().relative_to(self.contract.workspace).as_posix()
                    except ValueError:
                        continue
                    if rel not in protected:
                        protected.append(rel)
        return protected

    def _prompt(self) -> str:
        compact = self.contract.model_dump(mode="json", exclude={"workspace", "brief_file"})
        brief = self.contract.brief_file.read_text(encoding="utf-8") if self.contract.brief_file else ""
        return (
            "Execute this bounded coding contract. Do not use subagents, network calls, or commits. "
            "Stay within allowed_paths. Return JSON matching the supplied schema with status "
            "COMPLETED_WITH_EVIDENCE, BLOCKED, or DESIGN_CONFLICT, plus summary, changed_files, and evidence.\n"
            + json.dumps(compact, separators=(",", ":"))
            + ("\nBRIEF:\n" + brief if brief else "")
        )

    def _command(self) -> list[str]:
        if self.worker_command is not None:
            return self.worker_command
        executable = self.codex or shutil.which("codex")
        if not executable:
            raise RuntimeError("codex executable not found; pass --codex PATH")
        return [
            executable, "exec", "--model", self.contract.model, "--json",
            "--sandbox", "workspace-write", "--approve-for-me", "--skip-git-repo-check",
            "--output-schema", str(self.run_dir / "result.schema.json"),
            "--output-last-message", str(self.run_dir / "result.json"), "--cd", str(self.contract.workspace),
            self._prompt(),
        ]

    def _start_child(self, command: list[str], stdout_path: Path, stderr_path: Path, worker: bool = True) -> None:
        environment = os.environ.copy()
        environment["DEVCONTROL_RUN_DIR"] = str(self.run_dir)
        environment["DEVCONTROL_WORKSPACE"] = str(self.contract.workspace)
        if worker:
            environment["DEVCONTROL_RESULT_PATH"] = str(self.run_dir / "result.json")
        options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
        stdout = stdout_path.open("wb")
        stderr = stderr_path.open("wb")
        try:
            self.child = subprocess.Popen(command, cwd=self.contract.workspace, env=environment, stdout=stdout, stderr=stderr, **options)
        finally:
            stdout.close()
            stderr.close()

    def _wait_child(self, status: str = "RUNNING") -> str | int:
        assert self.child is not None
        self.state(status, child_pid=self.child.pid)
        while True:
            code = self.child.poll()
            if code is not None:
                return code
            if (self.run_dir / "STOP").exists():
                kill_tree(self.child.pid)
                self.child.wait()
                return "STOPPED"
            if self.remaining() <= 0:
                kill_tree(self.child.pid)
                self.child.wait()
                return "TIMED_OUT"
            time.sleep(.1)

    def _verification(self) -> tuple[bool, str]:
        commands = list(self.contract.verification_commands)
        if self.contract.semantic_review:
            commands.append([sys.executable, "-m", "devcontrol.semantic", "--run", str(self.run_dir)])
        if not commands:
            return False, "no acceptance check configured; a worker's claim alone cannot complete a task"
        records = []
        for index, command in enumerate(commands):
            if self.remaining() <= 0:
                return False, "deadline expired during verification"
            stdout_name = f"verification-{index}.stdout.log"
            stderr_name = f"verification-{index}.stderr.log"
            self._start_child(command, self.run_dir / stdout_name, self.run_dir / stderr_name, worker=False)
            outcome = self._wait_child("VERIFYING")
            if outcome == "TIMED_OUT":
                return False, "deadline expired during verification"
            if outcome == "STOPPED":
                return False, "stop requested during verification"
            records.append({"command": command, "exit_code": outcome, "stdout": stdout_name, "stderr": stderr_name})
            _atomic_json(self.run_dir / "verification.json", records)
            self.event("verification_finished", "VERIFYING", f"command {index + 1} exit {outcome}")
            if outcome != 0:
                return False, f"verification command {index + 1} exited {outcome}"
        return True, ""

    def execute(self) -> int:
        self.run_dir.mkdir(parents=True)
        try:
            self.lock.acquire()
        except RuntimeError:
            shutil.rmtree(self.run_dir, ignore_errors=True)
            raise
        try:
            contract_data = self.contract.model_dump(mode="json")
            _atomic_json(self.run_dir / "contract.json", contract_data)
            contract_bytes = (self.run_dir / "contract.json").read_bytes()
            (self.run_dir / "contract.sha256").write_text(hashlib.sha256(contract_bytes).hexdigest() + "\n", encoding="ascii")
            schema = WorkerReport.model_json_schema()
            _atomic_json(self.run_dir / "result.schema.json", schema)
            (self.run_dir / "prompt.txt").write_text(self._prompt(), encoding="utf-8")
            protected = self._implicit_protected()
            baseline = workspace_hashes(self.contract.workspace, self.contract.allowed_paths + protected)
            _atomic_json(self.run_dir / "baseline.json", {"files": baseline, "protected_paths": protected})
            self.state("RUNNING")
            self.event("worker_started", "RUNNING", f"model {self.contract.model}")
            self._start_child(self._command(), self.run_dir / "worker.stdout.log", self.run_dir / "worker.stderr.log")
            outcome = self._wait_child()
            if outcome in {"STOPPED", "TIMED_OUT"}:
                self.state(outcome, "stop requested" if outcome == "STOPPED" else "deadline exceeded")
                self.event("worker_stopped", outcome)
                return 1
            if outcome != 0:
                self.state("FAILED", f"worker exited {outcome}")
                self.event("worker_finished", "FAILED", f"exit {outcome}")
                return 1
            try:
                report = WorkerReport.model_validate_json((self.run_dir / "result.json").read_text(encoding="utf-8"))
            except (OSError, ValidationError, ValueError) as error:
                self.state("FAILED", f"invalid worker report: {error}")
                self.event("report_rejected", "FAILED", "invalid worker report")
                return 1
            if report.status != "COMPLETED_WITH_EVIDENCE":
                terminal = report.status
                self.state(terminal, report.summary, report=report.model_dump())
                self.event("worker_finished", terminal, report.summary)
                return 1
            final = workspace_hashes(self.contract.workspace, self.contract.allowed_paths + protected)
            changed = changed_paths(baseline, final)
            outside = [path for path in changed if not _path_in_scope(path, self.contract.allowed_paths)]
            protected_changed = [path for path in changed if _path_in_scope(path, protected)]
            _atomic_json(self.run_dir / "manifest.json", {"changed_paths": changed, "outside_scope": outside, "protected_changed": protected_changed, "final_hashes": final})
            if outside or protected_changed:
                details = "scope check failed: " + ", ".join(sorted(set(outside + protected_changed)))
                self.state("FAILED", details, report=report.model_dump())
                self.event("scope_rejected", "FAILED", details)
                return 1
            if not report.evidence:
                self.state("FAILED", "completion report has no evidence", report=report.model_dump())
                self.event("report_rejected", "FAILED", "empty evidence")
                return 1
            verified, details = self._verification()
            after_verification = workspace_hashes(self.contract.workspace, self.contract.allowed_paths + protected)
            verifier_changed = changed_paths(final, after_verification)
            verifier_outside = [path for path in verifier_changed if not _path_in_scope(path, self.contract.allowed_paths) or _path_in_scope(path, protected)]
            if verifier_outside:
                verified, details = False, "verification changed files outside scope: " + ", ".join(verifier_outside)
            if not verified:
                status = "TIMED_OUT" if details.startswith("deadline") else "STOPPED" if details.startswith("stop requested") else "FAILED"
                self.state(status, details, report=report.model_dump())
                self.event("completion_rejected", status, details)
                return 1
            self.state("COMPLETED", report.summary, report=report.model_dump(), changed_paths=changed)
            self.event("completed", "COMPLETED", report.summary)
            return 0
        finally:
            self.lock.release()
