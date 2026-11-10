import json

from credit_coach.bundle import LOCK_PATH, build_lock, verify_lock


def _files(tmp_path):
    (tmp_path / "a.txt").write_text("alpha")
    (tmp_path / "b.txt").write_text("beta")
    return {"a": "a.txt", "b": "b.txt"}


def test_intact_bundle_verifies(tmp_path):
    lock = build_lock(_files(tmp_path), tmp_path)
    assert verify_lock(lock, tmp_path) == []


def test_changed_file_is_detected(tmp_path):
    lock = build_lock(_files(tmp_path), tmp_path)
    (tmp_path / "b.txt").write_text("beta changed")
    problems = verify_lock(lock, tmp_path)
    assert len(problems) == 1 and "b: hash changed" in problems[0]


def test_missing_file_is_detected(tmp_path):
    lock = build_lock(_files(tmp_path), tmp_path)
    (tmp_path / "a.txt").unlink()
    assert "a: missing" in verify_lock(lock, tmp_path)[0]


def test_repo_lock_matches_files_when_present():
    """The committed bundle.lock.json must match the frozen files (this is the CI hash check)."""
    if not LOCK_PATH.exists():
        return
    assert verify_lock(json.loads(LOCK_PATH.read_text())) == []
