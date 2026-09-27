import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("path", [
    "data/news.json",
    "data/salt.bin",
    "secret/password.txt",
    "logs/run.log",
    ".venv/pyvenv.cfg",
])
def test_private_files_are_never_published(path):
    result = subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT)
    assert result.returncode == 0, f"{path} is not git-ignored"
