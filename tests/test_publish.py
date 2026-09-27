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
    (repo / "docs" / "index.html").write_text("page")
    return repo, remote


def site(remote, *args):
    return git("--git-dir", str(remote), *args)


def test_publish_puts_only_the_site_on_gh_pages(tmp_path):
    repo, remote = setup(tmp_path)
    (repo / "docs" / "news.enc").write_text("one")
    (repo / "docs" / "notes.txt").write_text("not part of the site")
    assert git_publish(repo, "update 1") is True
    assert site(remote, "ls-tree", "-r", "--name-only", "gh-pages").split() == [".nojekyll", "index.html", "news.enc"]
    assert site(remote, "show", "gh-pages:news.enc") == "one"


def test_each_publish_replaces_the_history(tmp_path):
    # hourly ciphertext never compresses; keeping history would outgrow GitHub's repo limit
    repo, remote = setup(tmp_path)
    (repo / "docs" / "news.enc").write_text("one")
    git_publish(repo, "update 1")
    (repo / "docs" / "news.enc").write_text("two")
    assert git_publish(repo, "update 2") is True
    assert site(remote, "log", "--oneline", "gh-pages").splitlines() == [
        site(remote, "log", "--oneline", "-1", "gh-pages").strip()]
    assert site(remote, "show", "gh-pages:news.enc") == "two"


def test_failed_push_is_recovered_next_run(tmp_path):
    repo, remote = setup(tmp_path)
    moved = tmp_path / "moved.git"
    (repo / "docs" / "news.enc").write_text("one")
    remote.rename(moved)                      # simulate: no internet / GitHub down
    assert git_publish(repo, "update 1") is False
    moved.rename(remote)                      # back online
    (repo / "docs" / "news.enc").write_text("two")
    assert git_publish(repo, "update 2") is True
    assert site(remote, "show", "gh-pages:news.enc") == "two"


def test_remote_edits_do_not_block_publishing(tmp_path):
    # e.g. the user edited something on the GitHub website
    repo, remote = setup(tmp_path)
    (repo / "docs" / "news.enc").write_text("one")
    git_publish(repo, "update 1")
    other = tmp_path / "other"
    git("clone", "-q", "-b", "gh-pages", str(remote), str(other))
    git("config", "user.name", "x", cwd=other)
    git("config", "user.email", "x@x", cwd=other)
    (other / "README.md").write_text("hi")
    git("add", "README.md", cwd=other)
    git("commit", "-qm", "web edit", cwd=other)
    git("push", "-q", "origin", "gh-pages", cwd=other)
    (repo / "docs" / "news.enc").write_text("two")
    assert git_publish(repo, "update 2") is True
    assert site(remote, "show", "gh-pages:news.enc") == "two"


def test_working_branch_and_staged_files_are_untouched(tmp_path):
    repo, remote = setup(tmp_path)
    (repo / "code.py").write_text("x = 1")
    git("add", "code.py", cwd=repo)
    git("commit", "-qm", "code", cwd=repo)
    (repo / "notes.txt").write_text("private")
    git("add", "notes.txt", cwd=repo)
    (repo / "docs" / "news.enc").write_text("one")
    git_publish(repo, "update 1")
    assert git("diff", "--cached", "--name-only", cwd=repo).split() == ["notes.txt"]
    assert len(git("log", "--oneline", "main", cwd=repo).splitlines()) == 1


def test_failure_reason_is_logged(tmp_path, caplog):
    repo, remote = setup(tmp_path)
    (repo / "docs" / "news.enc").write_text("one")
    remote.rename(tmp_path / "gone.git")
    with caplog.at_level("WARNING", logger="newsdesk"):
        assert git_publish(repo, "update 1") is False
    assert "git push failed" in caplog.text
    assert "fatal" in caplog.text.lower()


def test_missing_news_file_fails_cleanly(tmp_path, caplog):
    repo, remote = setup(tmp_path)
    with caplog.at_level("WARNING", logger="newsdesk"):
        assert git_publish(repo, "update 1") is False
    assert "news.enc" in caplog.text
