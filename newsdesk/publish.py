"""Commit docs/ and push it to GitHub without ever waiting for a login prompt."""
import os
import subprocess
import sys

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def _git(repo, *args, timeout=120):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    return subprocess.run(["git", *args], cwd=repo, env=env, capture_output=True, text=True,
                          timeout=timeout, creationflags=_NO_WINDOW)


def git_publish(repo, message):
    """Return True if docs/ is on GitHub. A failed push leaves the commit for the next run."""
    try:
        if _git(repo, "add", "docs").returncode != 0:
            return False
        if _git(repo, "diff", "--cached", "--quiet").returncode != 0:
            if _git(repo, "commit", "-m", message).returncode != 0:
                return False
        return _git(repo, "push", "origin", "HEAD").returncode == 0
    except subprocess.TimeoutExpired:
        return False
