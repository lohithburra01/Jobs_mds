import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


class RunStore:
    def __init__(self, folder: Path):
        self.folder = folder
        self.folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / "run.json"
        self.state = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {
            "schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "STARTED", "http_attempts": 0, "cost_usd": 0.0, "calls": [],
            "blocks": {}, "events": [], "calibration": "experimental_uncalibrated",
        }

    def save(self):
        atomic_json(self.path, self.state)

    def event(self, stage: str, **details):
        self.state["events"].append({"at": datetime.now(timezone.utc).isoformat(), "stage": stage, **details})
        self.save()

    def write(self, name: str, data):
        atomic_json(self.folder / name, data)

    def request(self, key: str, body: dict):
        self.write(f"requests/{key}.json", body)

    def response(self, key: str):
        path = self.folder / "responses" / f"{key}.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    def usage_snapshot(self):
        return {"at": time.monotonic(), "http_attempts": self.state.get("http_attempts", 0),
                "cost_usd": self.state.get("cost_usd", 0.0)}

    def begin_stage(self, stage: str):
        """Persist a usage baseline so a resumed process keeps earlier stage calls."""
        usage = self.state.setdefault("stage_usage", [])
        pending = self.state.setdefault("pending_stage_usage", {})
        if any(item["stage"] == stage for item in usage):
            pending.pop(stage, None)
            self.save()
            return None
        if stage not in pending:
            pending[stage] = {
                "started_at": time.time(),
                "http_attempts": self.state.get("http_attempts", 0),
                "cost_usd": self.state.get("cost_usd", 0.0),
            }
            self.save()
        return pending[stage]

    def record_stage(self, stage: str, before: dict | None = None):
        usage = self.state.setdefault("stage_usage", [])
        if any(item["stage"] == stage for item in usage):
            return
        pending = self.state.setdefault("pending_stage_usage", {})
        baseline = pending.pop(stage, None) or before
        if baseline is None:
            raise ValueError(f"Stage {stage!r} has no persisted usage baseline")
        if "started_at" in baseline:
            elapsed = time.time() - baseline["started_at"]
        else:
            elapsed = time.monotonic() - baseline["at"]
        usage.append({"stage": stage,
                      "http_attempts": self.state.get("http_attempts", 0) - baseline["http_attempts"],
                      "reported_cost_usd": self.state.get("cost_usd", 0.0) - baseline["cost_usd"],
                      "elapsed_seconds": round(max(0.0, elapsed), 3)})
        self.save()
