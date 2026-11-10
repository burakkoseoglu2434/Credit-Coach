import shutil
import subprocess
import sys

import pytest
import yaml
from sqlalchemy import text

from credit_coach.bundle import LOCK_PATH
from credit_coach.bundle import sha256 as file_sha256
from credit_coach.decision_log import GENESIS_HASH, current_bundle_sha256, policy_file_sha256
from credit_coach.policy import POLICY_DIR, load_policy
from credit_coach.replay import default_loader, replay
from tests.test_decision_log import _girdi, _rec


def _fill(app, n=3):
    return [_rec(app, _girdi(0.05 + i / 40))[0] for i in range(n)]


def test_clean_log_replays_byte_for_byte(db):
    _, app = db
    _fill(app, 4)
    with app.connect() as c:
        r = replay(c)
    assert (r.chain_ok, r.checked, r.matched, r.differences, r.errors) == (True, 4, 4, [], [])
    assert r.exit_code == 0
    assert "karar katmanı" in r.render() and "Skor katmanı bu raporda YOK" in r.render()


def test_replay_works_with_select_only_role_and_single_id(db):
    _, app = db
    rows = _fill(app, 2)
    with app.connect() as c:
        r = replay(c, decision_id=rows[1].decision_id)
    assert r.checked == 1 and r.exit_code == 0


def test_stored_decision_tampered_is_caught_by_chain_and_replay(db):
    owner, app = db
    _fill(app, 3)
    with owner.begin() as c:
        c.execute(text("ALTER TABLE decision_log DISABLE TRIGGER ALL"))
        c.execute(
            text("""UPDATE decision_log SET cikti_json = regexp_replace(
            cikti_json, '"dis_durum":"[A-Z]+"', '"dis_durum":"ZZZ"') WHERE seq = 2""")
        )
        c.execute(text("ALTER TABLE decision_log ENABLE TRIGGER ALL"))
    with app.connect() as c:
        r = replay(c)
    assert r.exit_code == 2 and not r.chain_ok  # chain first: no replay on a broken chain
    assert r.checked == 0

    # a forger who also repairs the hashes defeats the chain but NOT replay
    from credit_coach.decision_log import compute_row_hash

    with owner.begin() as c:
        c.execute(text("ALTER TABLE decision_log DISABLE TRIGGER ALL"))
        rows = c.execute(text("SELECT * FROM decision_log ORDER BY seq")).mappings().all()
        prev = GENESIS_HASH
        for row in rows:
            d = {
                k: row[k]
                for k in (
                    "decision_id",
                    "kayit_zamani",
                    "girdi_json",
                    "cikti_json",
                    "politika_surumu",
                    "politika_sha256",
                    "bundle_sha256",
                )
            }
            new = compute_row_hash(**d, prev_hash=prev)
            c.execute(
                text("UPDATE decision_log SET prev_hash='x'||substr(prev_hash,2) WHERE seq=:s"),
                {"s": row["seq"]},
            )  # avoid UNIQUE clashes
            c.execute(
                text("UPDATE decision_log SET prev_hash=:p, row_hash=:h WHERE seq=:s"),
                {"p": prev, "h": new, "s": row["seq"]},
            )
            prev = new
        c.execute(text("ALTER TABLE decision_log ENABLE TRIGGER ALL"))
    with app.connect() as c:
        r = replay(c)
    assert r.chain_ok and r.exit_code == 1
    assert [(d.seq, d.field, d.stored) for d in r.differences] == [(2, "dis_durum", "ZZZ")]


def test_changed_policy_file_stops_with_explicit_error(db, tmp_path):
    _, app = db
    _fill(app, 2)
    shutil.copy(POLICY_DIR / "v1.yaml", tmp_path / "v1.yaml")
    doc = yaml.safe_load((tmp_path / "v1.yaml").read_text())
    doc["onay_esigi"] = 0.2  # silently different threshold
    (tmp_path / "v1.yaml").write_text(yaml.safe_dump(doc))
    with app.connect() as c:
        r = replay(c, loader=default_loader(tmp_path))
    assert r.exit_code == 1 and r.matched == 0 and r.differences == []
    assert {e.kind for e in r.errors} == {"POLICY_FILE_HASH_MISMATCH"}


def test_unknown_policy_version_is_an_error_not_a_default(db, tmp_path):
    _, app = db
    _fill(app, 1)
    with app.connect() as c:
        r = replay(c, loader=default_loader(tmp_path))  # empty policy dir
    assert [e.kind for e in r.errors] == ["POLICY_UNKNOWN"]


def test_v1_records_still_replay_after_v2_is_added(db, tmp_path):
    _, app = db
    _fill(app, 3)
    for f in POLICY_DIR.glob("v*.yaml"):
        shutil.copy(f, tmp_path / f.name)
    v2 = yaml.safe_load((tmp_path / "v1.yaml").read_text())
    v2.update(surum="v2", onay_esigi=0.05, ret_esigi=0.3)
    (tmp_path / "v2.yaml").write_text(yaml.safe_dump(v2))
    assert load_policy("v2", tmp_path).onay_esigi == 0.05  # v2 exists
    with app.connect() as c:
        r = replay(c, loader=default_loader(tmp_path))
    assert r.exit_code == 0 and r.matched == 3  # v1 records still replay under frozen v1


def test_frozen_v1_file_matches_bundle_lock():
    import json

    lock = json.loads(LOCK_PATH.read_text())
    entry = next(v for v in lock["files"].values() if v["path"] == "configs/policy/v1.yaml")
    assert policy_file_sha256("v1") == entry["sha256"]


def test_changed_bundle_is_reported_not_failed(db):
    _, app = db
    from credit_coach.decision_log import record_decision

    record_decision(app, _girdi(), load_policy("v1"), policy_file_sha256("v1"))
    with app.begin() as c:  # an older record written under another bundle
        from credit_coach.decision_log import append

        append(
            c,
            girdi_json=_rec_json(),
            cikti_json=_out_json(),
            politika_surumu="v1",
            politika_sha256=policy_file_sha256("v1"),
            bundle_sha256="f" * 64,
        )
    with app.connect() as c:
        r = replay(c)
    assert r.exit_code == 0
    assert any("FARKLI" in n for n in r.bundle_notes) and any("aynı" in n for n in r.bundle_notes)


def _rec_json():
    from credit_coach.canonical import model_canonical_text

    return model_canonical_text(_girdi())


def _out_json():
    from credit_coach.canonical import model_canonical_text
    from credit_coach.decision_engine import decide

    return model_canonical_text(decide(_girdi(), load_policy("v1")))


def test_cli_exit_codes(db):
    import os

    owner, app = db
    _fill(app, 2)
    env = {**os.environ}
    cmd = [sys.executable, "-m", "credit_coach.replay", "--all"]
    ok = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    with owner.begin() as c:
        c.execute(text("ALTER TABLE decision_log DISABLE TRIGGER ALL"))
        c.execute(text("UPDATE decision_log SET cikti_json = '{}' WHERE seq = 1"))
        c.execute(text("ALTER TABLE decision_log ENABLE TRIGGER ALL"))
    bad = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert bad.returncode == 2 and "BOZUK" in bad.stdout


def test_bundle_hash_helpers_are_stable():
    assert current_bundle_sha256() == file_sha256(LOCK_PATH)


@pytest.fixture(autouse=True)
def _pythonpath(monkeypatch):
    monkeypatch.setenv("PYTHONPATH", "src")
