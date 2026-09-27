from contextlib import contextmanager, closing
from collections import deque
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import time
import uuid


def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


class UnknownRecord(ValueError):
    pass


class Store:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.home = self.root / "project-memory"
        for name in ("records", "cache", "events"):
            (self.home / name).mkdir(parents=True, exist_ok=True)

    @contextmanager
    def lock(self):
        """OS-released lock: crashed processes never leave a stale PID lock."""
        with (self.home / "store.lock").open("a+b") as f:
            if f.tell() == 0:
                f.write(b"0")
                f.flush()
            deadline = time.monotonic() + 10
            while True:
                try:
                    f.seek(0)
                    if os.name == "nt":
                        import msvcrt
                        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise ValueError("Memory is busy. Retry; do not remove its lock file.")
                    time.sleep(.05)
            try:
                yield
            finally:
                f.seek(0)
                if os.name == "nt":
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def validate_id(self, ident):
        if not isinstance(ident, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,99}", ident):
            raise ValueError("Record ID must be lowercase letters, numbers and hyphens.")
        return ident

    def path(self, relative):
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Source must stay inside the project.")
        if any(p.lower() == ".env" or p.lower().startswith(".env.") or p.lower() == ".git" for p in path.parts):
            raise ValueError("Secret/environment and Git internal files cannot be imported.")
        return path

    def get(self, ident, revision=None):
        directory = self.home / "records" / self.validate_id(ident)
        files = sorted(directory.glob("[0-9]*.json"))
        if not files:
            raise UnknownRecord("Unknown record: " + ident)
        file = directory / f"{revision:06d}.json" if revision else files[-1]
        record = json.loads(file.read_text(encoding="utf-8"))
        self._validate_record_shape(record, ident, int(file.stem))
        return record

    def all(self):
        return [self.get(p.name) for p in sorted((self.home / "records").iterdir())
                if p.is_dir() and any(p.glob("[0-9]*.json"))]

    def _event(self, kind, summary, record=None, **extra):
        event = dict(id=uuid.uuid4().hex, time=now(), kind=kind, summary=summary[:1000], record=record, **extra)
        path = self.home / "events" / (event["time"][:10] + ".jsonl")
        with path.open("a+b") as f:
            if f.tell():
                f.seek(-1, os.SEEK_END)
                if f.read(1) != b"\n":
                    f.write(b"\n")  # Preserve a torn line, but isolate the next valid event.
            f.write((json.dumps(event, ensure_ascii=False) + "\n").encode("utf-8"))
            f.flush()
            os.fsync(f.fileno())
        return event

    def event(self, kind, summary, record=None, **extra):
        with self.lock():
            if record:
                self.get(record)
            return self._event(kind, summary, record, **extra)

    def put(self, data, expected_revision, reason):
        data = dict(data)
        self._validate_record_shape(data)
        ident = self.validate_id(data.get("id"))
        if not reason.strip():
            raise ValueError("Explain why this record is changing.")
        for field in ("kind", "title", "summary"):
            if not isinstance(data.get(field), str) or not data[field].strip():
                raise ValueError("Missing " + field)
        if len(data["summary"]) > 1200:
            raise ValueError("Keep the summary under 1200 characters; use body for detail.")
        if not isinstance(data.get("body", ""), str):
            raise ValueError("Record body must be text.")
        allowed = {"", "planned", "in_progress", "review", "accepted", "historical", "reference", "active", "proposed", "needs_review", "blocked", "deferred", "superseded"}
        if data.get("status", "") not in allowed:
            raise ValueError("Unknown status")
        if data.get("status") == "accepted" and not data.get("acceptance", {}).get("user_statement"):
            raise ValueError("Acceptance needs the user's statement; technical success is not acceptance.")
        with self.lock():
            try:
                previous = self.get(ident)
            except UnknownRecord:
                previous = None
            actual = previous["revision"] if previous else 0
            if actual != expected_revision:
                raise ValueError(f"Stale revision for {ident}: expected {expected_revision}, current {actual}. Read it again.")
            for edge in data.get("links", []):
                if not edge.get("rel") or edge["to"] == ident:
                    raise ValueError("Links require a relationship and a different target.")
                self.get(edge["to"])
            for source in data.get("sources", []):
                self.source_text(source)
            if data["kind"] == "project":
                self.get(data["focus"])
                for checkpoint in data.get("checkpoints", []):
                    self.get(checkpoint)
            data.update(revision=actual + 1, updated_at=now(), change_reason=reason)
            directory = self.home / "records" / ident
            directory.mkdir(exist_ok=True)
            target = directory / f"{actual + 1:06d}.json"
            if target.exists():
                raise ValueError("Revision already exists; refusing to overwrite history.")
            temporary = directory / ("." + uuid.uuid4().hex + ".tmp")
            with temporary.open("w", encoding="utf-8", newline="\n") as f:
                f.write(dump(data))
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporary, target)
            self._event("record_updated", reason, ident, revision=actual + 1)
        return data

    def _validate_source(self, source):
        if not isinstance(source, dict):
            raise ValueError("Source reference must be an object.")
        if not isinstance(source.get("path"), str) or not source["path"].strip():
            raise ValueError("Source reference needs a path.")
        self.path(source["path"])
        if not isinstance(source.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", source["sha256"]):
            raise ValueError("Source reference needs a SHA-256 hash.")
        for field in ("start", "end"):
            if field in source and (type(source[field]) is not int or source[field] < 1):
                raise ValueError("Source " + field + " must be a positive line number.")
        if source.get("end", source.get("start", 1)) < source.get("start", 1):
            raise ValueError("Source end must not precede start.")

    def _validate_record_shape(self, data, ident=None, revision=None):
        if not isinstance(data, dict):
            raise ValueError("Record must be an object.")
        self.validate_id(data.get("id"))
        if ident is not None and data["id"] != ident:
            raise ValueError("Record ID does not match its directory.")
        if revision is not None and (type(data.get("revision")) is not int or data["revision"] != revision):
            raise ValueError("Record revision does not match its filename.")
        for field in ("kind", "title", "summary"):
            if not isinstance(data.get(field), str) or not data[field].strip():
                raise ValueError("Missing " + field)
        if not isinstance(data.get("body", ""), str):
            raise ValueError("Record body must be text.")
        for field in ("links", "sources"):
            if not isinstance(data.get(field, []), list):
                raise ValueError("Record " + field + " must be a list.")
        for edge in data.get("links", []):
            if not isinstance(edge, dict) or not isinstance(edge.get("rel"), str) or not edge["rel"].strip():
                raise ValueError("Link requires a relationship.")
            self.validate_id(edge.get("to"))
            if edge["to"] == data["id"]:
                raise ValueError("Link must target a different record.")
        for source in data.get("sources", []):
            self._validate_source(source)

    def source_text(self, source):
        self._validate_source(source)
        raw = self.path(source["path"]).read_bytes()
        if digest(raw) != source["sha256"]:
            raise ValueError("Source changed: " + source["path"] + "; review/reimport before relying on its old line ranges.")
        lines = raw.decode("utf-8-sig").splitlines(keepends=True)
        if source.get("start", 1) > len(lines) or source.get("end", len(lines)) > len(lines):
            raise ValueError("Source line range exceeds file length: " + source["path"])
        return "".join(lines[source.get("start", 1)-1:source.get("end", len(lines))])

    def rebuild(self):
        with self.lock():
            records = self.all()
            cache = self.home / "cache" / "memory.sqlite3"
            temporary = cache.with_name(uuid.uuid4().hex + ".sqlite3")
            with closing(sqlite3.connect(temporary)) as conn:
                with conn:
                    conn.execute("CREATE TABLE IF NOT EXISTS nodes (id TEXT PRIMARY KEY, kind TEXT, title TEXT, status TEXT, content TEXT)")
                    conn.execute("CREATE TABLE IF NOT EXISTS edges (source TEXT, relation TEXT, target TEXT)")
                    conn.execute("DELETE FROM nodes")
                    conn.execute("DELETE FROM edges")
                    for r in records:
                        content = r["summary"] + "\n" + r.get("body", "")
                        for s in r.get("sources", []):
                            try:
                                content += "\n" + self.source_text(s)
                            except (OSError, ValueError):
                                pass  # doctor reports stale sources; never indexes changed text as agreed text.
                        conn.execute("INSERT INTO nodes VALUES (?,?,?,?,?)", (r["id"], r["kind"], r["title"], r.get("status", ""), content))
                        conn.executemany("INSERT INTO edges VALUES (?,?,?)", [(r["id"], e["rel"], e["to"]) for e in r.get("links", [])])
            os.replace(temporary, cache)
        return {"records": len(records), "index": "project-memory/cache/memory.sqlite3", "truth": "versioned JSON records"}

    def search(self, query, limit=12):
        if not 1 <= limit <= 100:
            raise ValueError("Search limit must be 1–100.")
        self.rebuild()
        with closing(sqlite3.connect(self.home / "cache" / "memory.sqlite3")) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(r) for r in conn.execute("SELECT id,kind,title,status FROM nodes WHERE instr(lower(title || ' ' || content),lower(?))>0 ORDER BY CASE WHEN status IN ('historical','superseded') THEN 2 ELSE 0 END, CASE WHEN kind IN ('rule','module','checkpoint','decision') THEN 0 WHEN kind='source_section' THEN 1 ELSE 2 END, id LIMIT ?", (query, limit))]

    def impact(self, ident):
        self.get(ident)
        records = self.all()
        visited, frontier = {ident}, [ident]
        while frontier:
            target = frontier.pop()
            for r in records:
                if r["id"] not in visited and any(e["to"] == target and e["rel"] in {"depends_on", "uses", "implements"} for e in r.get("links", [])):
                    visited.add(r["id"])
                    frontier.append(r["id"])
        return {"changed_id": ident, "affected_ids": sorted(visited - {ident}), "limit": "Known recorded dependencies only. Inspect code and other sources before claiming complete impact. Nothing was modified."}

    def timeline(self, limit=15):
        if not 1 <= limit <= 1000:
            raise ValueError("Timeline limit must be 1–1000.")
        rows = []
        for path in sorted((self.home / "events").glob("*.jsonl"), reverse=True):
            with path.open(encoding="utf-8", errors="replace") as f:
                tail = deque(f, maxlen=limit-len(rows))
            for line in reversed(tail):
                try:
                    item = json.loads(line)
                    if not isinstance(item, dict) or not all(k in item for k in ("time", "kind", "summary")):
                        raise ValueError("Invalid event")
                    rows.append(item)
                except ValueError:
                    rows.append({"time": path.stem + " (time unknown)", "kind": "damaged_event", "summary": "Incomplete event line; inspect " + path.name})
                if len(rows) >= limit:
                    return rows
        return rows

    def doctor(self):
        problems = []
        records = []
        for path in sorted((self.home / "records").iterdir()):
            if path.is_dir():
                revisions = sorted(path.glob("[0-9]*.json"))
                if not revisions:
                    problems.append(path.name + ": no saved revisions")
                for saved in revisions:
                    try:
                        record = json.loads(saved.read_text(encoding="utf-8"))
                        self._validate_record_shape(record, path.name, int(saved.stem))
                        if saved == revisions[-1]:
                            records.append(record)
                    except (ValueError, OSError) as exc:
                        problems.append(path.name + "/" + saved.name + ": incomplete or damaged record: " + str(exc))
                if any(path.glob("*.tmp")):
                    problems.append(path.name + ": interrupted temporary write retained for inspection")
        known = {r["id"] for r in records}
        for r in records:
            for edge in r.get("links", []):
                if edge["to"] not in known:
                    problems.append(r["id"] + ": broken link " + edge["to"])
            for source in r.get("sources", []):
                try:
                    self.source_text(source)
                except (OSError, ValueError) as exc:
                    problems.append(r["id"] + ": source unavailable or changed: " + str(exc))
        return {"records": len(records), "problems": problems,
                "limit": "Checks record integrity, not correctness of the plan or quality of the application."}

    def brief(self, ident=None):
        project = self.get("project")
        ident = ident or project["focus"]
        active = self.get(ident)
        lines = ["PROJECT: " + project["title"], "GOAL: " + project["summary"],
                 "CURRENT: " + active["id"] + " — " + active["title"] + " [" + active.get("status", "not started") + "]",
                 "STATE: " + active["summary"], "NEXT: " + active.get("next_action", "Discuss this checkpoint with Lohith."),
                 "\nCHECKPOINTS:"]
        for key in project.get("checkpoints", []):
            r = self.get(key)
            lines.append(f"  {key}: {r['title']} — {r.get('status') or 'not started'}")
        lines.append("\nWORKING RULES:")
        for edge in project.get("links", []):
            if edge["rel"] == "rule":
                r = self.get(edge["to"])
                lines.append(r["id"] + ": " + r["summary"])
        lines.append("\nACTIVE DESIGN DECISIONS:")
        for edge in project.get("links", []):
            if edge["rel"] == "decision":
                r = self.get(edge["to"])
                if r.get("status") == "active":
                    lines.append(r["id"] + ": " + r["summary"])
        lines.extend(["\nCURRENT DETAIL:", active.get("body", ""), "\nREAD NEXT (retrieve just what you need):"])
        for edge in active.get("links", []):
            r = self.get(edge["to"])
            lines.append(f"  {r['id']}: {r['title']} ({edge['rel']})")
        lines.append("\nUse scripts/project-memory.ps1 show ID, source ID, search TEXT, impact ID, timeline, doctor. Source archives are evidence, not current execution instructions. Latest explicit user instructions prevail. Acceptance is Lohith's decision. No requirement to use a particular model.")
        result = "\n".join(lines)
        if len(result) > 10000:
            result = result[:9600] + "\n[Briefing capped. Read show project and show " + ident + " for full records.]"
        return result

    def import_source(self, relative, ident, status="reference", snapshot=False, ranges=None):
        original = self.path(relative)
        raw = original.read_bytes()
        text = raw.decode("utf-8-sig")
        lines = text.splitlines(keepends=True)
        if snapshot:
            relative = f"project-memory/sources/{ident}.txt"
            frozen = self.path(relative)
            frozen.parent.mkdir(exist_ok=True)
            if frozen.exists() and frozen.read_bytes() != raw:
                raise ValueError("Snapshot already exists with different content; choose a new source ID.")
            frozen.write_bytes(raw)
        source = dict(path=str(relative).replace("\\", "/"), sha256=digest(raw), start=1, end=len(lines))
        parent = dict(id=ident, kind="source", title=original.name, summary="Original source, retrieved by exact section. Later user decisions can supersede its instructions.", status=status,
                      body="Source preserved without paraphrasing. Original path: " + str(original.relative_to(self.root)), sources=[source], links=[])
        self.put(parent, 0, "Import source without changing its text")
        if ranges is None:
            starts = sorted(set([1] + [i for i, line in enumerate(lines, 1) if re.match(r"^#{1,3} ", line)] + list(range(1, len(lines)+1, 70))))
            ranges = [(start, (starts[n+1]-1 if n+1 < len(starts) else len(lines)), lines[start-1].strip()[:130] or "Continuation") for n, start in enumerate(starts)]
        for n, (start, end, title) in enumerate(ranges, 1):
            item = dict(id=f"{ident}-{n:03d}", kind="source_section", title=title, status=status,
                        summary=f"Exact source lines {start}–{end}; read with source command. Parent: {ident}.",
                        body="", sources=[dict(source, start=start, end=end)], links=[{"rel": "part_of", "to": ident}])
            self.put(item, 0, "Index a source section for selective retrieval")
        return {"source": ident, "sections": len(ranges), "sha256": source["sha256"]}
