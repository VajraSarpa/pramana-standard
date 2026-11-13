"""Loads the harness adapter named by PRAMANA_ADAPTER=module:Class. There is no default."""
import importlib
import os
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))


def pytest_configure(config):
    if not os.environ.get("PRAMANA_ADAPTER"):
        raise pytest.UsageError("set PRAMANA_ADAPTER=module:Class to the adapter for the harness under test "
                                "(see conformance/README.md)")


needs_bwrap = pytest.mark.skipif(shutil.which("bwrap") is None, reason="bwrap not installed")


@pytest.fixture
def h(tmp_path):
    mod, cls = os.environ["PRAMANA_ADAPTER"].split(":")
    return getattr(importlib.import_module(mod), cls)(tmp_path / "harness")


@pytest.fixture
def wt(h, tmp_path):
    return h.worktree(tmp_path, {"src/app.py": "def add(a, b):\n    return a + b\n",
                                 "tests/test_app.py": "from app import add\n\ndef test_add():\n    assert add(1, 2) == 3\n",
                                 ".env": "TOKEN=not-a-real-token\n"})
