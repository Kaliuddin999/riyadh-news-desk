"""Publish the site to the gh-pages branch without ever waiting for a login prompt.

The branch always holds exactly one commit: the current page and news. Hourly
ciphertext never compresses, so keeping history would outgrow GitHub's repo limit.
Every run publishes the full current state, so a failed push loses nothing.
"""
import logging
import os
import subprocess
import sys

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
BRANCH = "gh-pages"
SITE_FILES = (".nojekyll", "index.html", "news.enc")
log = logging.getLogger("newsdesk")


class _GitError(Exception):
    pass


def _git(repo, *args, env=None, timeout=120):
    full_env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never", **(env or {}))
    result = subprocess.run(["git", *args], cwd=repo, env=full_env, capture_output=True,
                            encoding="utf-8", errors="replace", timeout=timeout,
                            creationflags=_NO_WINDOW)
    if result.returncode != 0:
        raise _GitError(f"git {args[0]} failed ({result.returncode}): {result.stderr.strip()[:500]}")
    return result.stdout.strip()


def git_publish(repo, message):
    """Return True if the site is on GitHub. Never touches the working branch or its index."""
    docs = repo / "docs"
    try:
        (docs / ".nojekyll").touch(exist_ok=True)
        missing = [name for name in SITE_FILES if not (docs / name).exists()]
        if missing:
            raise _GitError(f"missing site file(s): {', '.join(missing)}")
        # Build the tree in a private index so the user's staged files are left alone.
        site_index = {"GIT_INDEX_FILE": os.path.join(_git(repo, "rev-parse", "--absolute-git-dir"), "site-index")}
        _git(repo, "read-tree", "--empty", env=site_index)
        for name in SITE_FILES:
            blob = _git(repo, "hash-object", "-w", str(docs / name))
            _git(repo, "update-index", "--add", "--cacheinfo", f"100644,{blob},{name}", env=site_index)
        tree = _git(repo, "write-tree", env=site_index)
        commit = _git(repo, "commit-tree", tree, "-m", message)
        _git(repo, "push", "--force", "origin", f"{commit}:refs/heads/{BRANCH}")
    except (_GitError, OSError, subprocess.TimeoutExpired) as exc:
        log.warning("publish failed: %s", exc)
        return False
    try:  # drop old unreferenced site snapshots from the local .git
        _git(repo, "prune", "--expire=1.day.ago")
    except (_GitError, OSError, subprocess.TimeoutExpired) as exc:
        log.warning("git prune failed: %s", exc)
    return True
