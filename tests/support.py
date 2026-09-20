"""Scratch paths with inherited Windows ACLs (tempfile's 0700 ACL excludes the sandbox)."""
import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def scratch():
    root = (Path(__file__).resolve().parents[1] / "tmp").resolve()
    root.mkdir(exist_ok=True)
    path = root / ("test-" + uuid.uuid4().hex)
    path.mkdir()
    try:
        yield path
    finally:
        if path.resolve().is_relative_to(root) and path != root:
            shutil.rmtree(path)
