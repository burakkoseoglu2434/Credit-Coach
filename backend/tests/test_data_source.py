import re
import subprocess

from credit_coach.data_source import ROOT, load_sources, rejected_path

HEX = re.compile(r"^[0-9a-f]{64}$")


def test_recorded_hashes_are_sha256_hex():
    e = load_sources()["lc_reddedilen"]
    assert HEX.match(e["sha256"]) and HEX.match(e["yan_dosya_accepted"]["sha256"])


def test_rejected_sits_next_to_accepted_in_the_same_archive():
    e = load_sources()["lc_reddedilen"]
    a = e["yan_dosya_accepted"]["yol"].rsplit("/", 2)[0]
    r = e["yol"].rsplit("/", 2)[0]
    assert a == r


def test_nothing_from_the_source_is_copied_into_the_repo():
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.lower()
    assert "rejected_2007" not in tracked and "accepted_2007" not in tracked


def test_size_matches_when_file_is_present():
    p = rejected_path()
    if p.exists():
        assert p.stat().st_size == load_sources()["lc_reddedilen"]["boyut_bayt"]
