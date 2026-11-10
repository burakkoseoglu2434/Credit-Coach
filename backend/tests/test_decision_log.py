import json
import threading

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from credit_coach.canonical import canonical_text, model_canonical_text
from credit_coach.contract import DecisionInput, parse_input
from credit_coach.decision_engine import decide
from credit_coach.decision_log import (
    GENESIS_HASH,
    ChainBroken,
    append,
    policy_file_sha256,
    read_all,
    read_one,
    record_decision,
    verify_chain,
)
from credit_coach.decision_scenarios import sample_basvuru
from credit_coach.policy import load_policy


def _girdi(p_point: float = 0.1042, ham: float = 0.3300000000000001) -> DecisionInput:
    return parse_input(
        {
            "basvuru": sample_basvuru(),
            "p_low": min(0.0913, p_point),
            "p_point": p_point,
            "p_high": max(0.1188, p_point),
            "ham_skor": ham,
            "politika_surumu": "v1",
            "plan_available": None,
        }
    )


def _rec(app, g=None, now="2026-11-10T12:00:00.000000Z"):
    p = load_policy("v1")
    return record_decision(app, g or _girdi(), p, policy_file_sha256("v1"), now=lambda: now)


def test_chain_links_and_verifies(db):
    owner, app = db
    rows = [_rec(app, _girdi(0.05 + i / 100))[0] for i in range(4)]
    assert rows[0].prev_hash == GENESIS_HASH
    assert [r.prev_hash for r in rows[1:]] == [r.row_hash for r in rows[:-1]]
    with app.connect() as c:
        assert verify_chain(c) == 4


def test_time_is_assigned_by_record_layer_not_decide(db):
    _, app = db
    g = _girdi()
    r1, k1 = _rec(app, g, "2026-01-01T00:00:00.000000Z")
    r2, k2 = _rec(app, g, "2027-01-01T00:00:00.000000Z")
    assert k1 == k2 and r1.cikti_json == r2.cikti_json
    assert r1.kayit_zamani != r2.kayit_zamani and r1.row_hash != r2.row_hash


def test_round_trip_record_db_read_reserialize_is_byte_exact(db):
    _, app = db
    g = _girdi(0.1 + 0.2 - 0.2, 0.30000000000000004)  # awkward floats on purpose
    row, karar = _rec(app, g)
    with app.connect() as c:
        got = read_one(c, row.decision_id)
    assert got == row
    assert got.girdi_json == model_canonical_text(g)
    assert canonical_text(json.loads(got.girdi_json)) == got.girdi_json
    again = DecisionInput.model_validate(json.loads(got.girdi_json))
    assert model_canonical_text(again) == got.girdi_json
    assert model_canonical_text(decide(again, load_policy("v1"))) == got.cikti_json
    assert got.cikti_json == model_canonical_text(karar)


def test_girdi_has_only_model_inputs_no_identity(db):
    _, app = db
    row, _ = _rec(app)
    girdi = json.loads(row.girdi_json)
    assert set(girdi) == {
        "basvuru",
        "p_low",
        "p_point",
        "p_high",
        "ham_skor",
        "politika_surumu",
        "plan_available",
    }
    from credit_coach.features import allowed_features

    assert set(girdi["basvuru"]) == set(allowed_features())


# ---- immutability: negative tests run as the INSERT/SELECT-only app role ----


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE decision_log SET cikti_json = 'x'",
        "DELETE FROM decision_log",
        "TRUNCATE decision_log",
        "DROP TABLE decision_log",
        "ALTER TABLE decision_log DISABLE TRIGGER ALL",
        "SET session_replication_role = replica",
    ],
)
def test_app_role_cannot_mutate(db, sql):
    _, app = db
    _rec(app)
    with pytest.raises(DBAPIError) as e, app.begin() as c:
        c.execute(text(sql))
    assert "permission denied" in str(e.value) or "must be" in str(e.value)
    with app.connect() as c:
        assert verify_chain(c) == 1


def test_app_role_has_exactly_select_and_insert(db):
    owner, _ = db
    with owner.connect() as c:
        privs = {
            r[0]
            for r in c.execute(
                text(
                    "SELECT privilege_type FROM information_schema.role_table_grants "
                    "WHERE grantee = 'cc_app' AND table_name = 'decision_log'"
                )
            )
        }
        rolsuper = c.execute(text("SELECT rolsuper FROM pg_roles WHERE rolname='cc_app'")).scalar()
    assert privs == {"SELECT", "INSERT"} and rolsuper is False


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE decision_log SET cikti_json = 'x'",
        "DELETE FROM decision_log",
        "TRUNCATE decision_log",
    ],
)
def test_trigger_blocks_even_the_owner(db, sql):
    owner, app = db
    _rec(app)
    with pytest.raises(DBAPIError) as e, owner.begin() as c:
        c.execute(text(sql))
    assert "append-only" in str(e.value)


def test_tampering_is_detected_by_verify(db):
    owner, app = db
    for i in range(3):
        _rec(app, _girdi(0.05 + i / 100))
    with owner.begin() as c:  # a superuser who removes the trigger can still rewrite...
        c.execute(text("ALTER TABLE decision_log DISABLE TRIGGER ALL"))
        c.execute(text("UPDATE decision_log SET cikti_json = '{}' WHERE seq = 2"))
        c.execute(text("ALTER TABLE decision_log ENABLE TRIGGER ALL"))
    with app.connect() as c, pytest.raises(ChainBroken):  # ...but the chain exposes it
        verify_chain(c)


# ---- concurrency ----


def test_concurrent_appends_form_one_linear_chain(db):
    _, app = db
    n_threads, per = 8, 6
    barrier = threading.Barrier(n_threads)
    errors: list[BaseException] = []

    def work(k: int) -> None:
        try:
            barrier.wait()
            for i in range(per):
                _rec(app, _girdi(0.01 + (k * per + i) / 1000))
        except BaseException as e:  # noqa: BLE001
            errors.append(e)

    ts = [threading.Thread(target=work, args=(k,)) for k in range(n_threads)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert not errors, errors
    with app.connect() as c:
        rows = read_all(c)
        assert verify_chain(c) == n_threads * per
    assert len({r.prev_hash for r in rows}) == len(rows)  # no fork


def test_two_concurrent_inserts_in_open_transactions_serialise(db):
    _, app = db
    first_in, release = threading.Event(), threading.Event()
    out: dict[str, str] = {}

    def a() -> None:
        with app.begin() as c:
            r = append(
                c, girdi_json="{}", cikti_json="{}", politika_surumu="v1", politika_sha256="s"
            )
            out["a"] = r.row_hash
            first_in.set()
            release.wait(5)

    def b() -> None:
        first_in.wait(5)
        with app.begin() as c:  # blocks on the advisory lock until a commits
            r = append(
                c, girdi_json="{}", cikti_json="{}", politika_surumu="v1", politika_sha256="s"
            )
            out["b_prev"] = r.prev_hash

    ta, tb = threading.Thread(target=a), threading.Thread(target=b)
    ta.start()
    tb.start()
    first_in.wait(5)
    tb.join(0.5)
    assert tb.is_alive(), "second insert must wait for the lock"
    release.set()
    ta.join()
    tb.join()
    assert out["b_prev"] == out["a"]


def test_fork_is_blocked_by_unique_prev_hash_even_without_the_lock(db):
    _, app = db
    _rec(app)
    with app.connect() as c:
        last = read_all(c)[-1]
    with pytest.raises(IntegrityError), app.begin() as c:  # bypass append(): reuse genesis link
        c.execute(
            text(
                "INSERT INTO decision_log (decision_id, kayit_zamani, girdi_json, cikti_json, "
                "politika_surumu, politika_sha256, bundle_sha256, prev_hash, row_hash) VALUES "
                "('x','t','{}','{}','v1','s','b', :p, :h)"
            ),
            {"p": GENESIS_HASH, "h": "a" * 64},
        )
    assert last.prev_hash == GENESIS_HASH
