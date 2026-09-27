import subprocess

from newsdesk.publish import git_publish


def git(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def setup(tmp_path):
    remote = tmp_path / "remote.git"
    git("init", "--bare", "-b", "main", str(remote))
    repo = tmp_path / "repo"
    repo.mkdir()
    git("init", "-b", "main", cwd=repo)
    git("config", "user.name", "test", cwd=repo)
    git("config", "user.email", "test@example.com", cwd=repo)
    git("remote", "add", "origin", str(remote), cwd=repo)
    (repo / "docs").mkdir()
    return repo, remote


def remote_log(remote):
    return git("--git-dir", str(remote), "log", "--oneline", "main")


def test_publish_commits_and_pushes(tmp_path):
    repo, remote = setup(tmp_path)
    (repo / "docs" / "news.enc").write_text("one")
    assert git_publish(repo, "update 1") is True
    assert "update 1" in remote_log(remote)


def test_only_docs_is_committed(tmp_path):
    repo, remote = setup(tmp_path)
    (repo / "docs" / "news.enc").write_text("one")
    (repo / "notes.txt").write_text("private")
    git_publish(repo, "update 1")
    files = git("--git-dir", str(remote), "ls-tree", "-r", "--name-only", "main")
    assert files.split() == ["docs/news.enc"]


def test_failed_push_is_retried_next_run(tmp_path):
    repo, remote = setup(tmp_path)
    moved = tmp_path / "moved.git"
    (repo / "docs" / "news.enc").write_text("one")
    remote.rename(moved)                      # simulate: no internet / GitHub down
    assert git_publish(repo, "update 1") is False
    moved.rename(remote)                      # back online
    (repo / "docs" / "news.enc").write_text("two")
    assert git_publish(repo, "update 2") is True
    log = remote_log(remote)
    assert "update 1" in log and "update 2" in log


def test_no_changes_is_still_success(tmp_path):
    repo, remote = setup(tmp_path)
    (repo / "docs" / "news.enc").write_text("one")
    assert git_publish(repo, "update 1") is True
    assert git_publish(repo, "update 2") is True
    assert "update 2" not in remote_log(remote)
