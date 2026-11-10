"""Append-only decision log with a SHA-256 hash chain (week 3.3).

Time and ids are assigned HERE, never inside decide(). girdi/cikti are stored as canonical
TEXT. Appends are serialised with a transaction-level advisory lock; UNIQUE(prev_hash) in the
schema is the second line of defence against forks.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import Connection, Engine, text

from credit_coach.bundle import sha256 as file_sha256
from credit_coach.canonical import canonical_text, model_canonical_text, sha256_hex
from credit_coach.contract import DecisionInput, InternalDecision
from credit_coach.decision_engine import decide
from credit_coach.policy import POLICY_DIR, Policy

GENESIS_HASH = "0" * 64
ADVISORY_LOCK_KEY = 0x43430001  # "CC" + 1: decision_log appends


class ChainBroken(Exception):
    """The stored chain does not verify."""


@dataclass(frozen=True)
class LogRow:
    seq: int
    decision_id: str
    kayit_zamani: str
    girdi_json: str
    cikti_json: str
    politika_surumu: str
    politika_sha256: str
    prev_hash: str
    row_hash: str


def policy_file_sha256(surum: str) -> str:
    return file_sha256(POLICY_DIR / f"{surum}.yaml")


def utc_now_text() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def compute_row_hash(
    *,
    decision_id: str,
    kayit_zamani: str,
    girdi_json: str,
    cikti_json: str,
    politika_surumu: str,
    politika_sha256: str,
    prev_hash: str,
) -> str:
    return sha256_hex(
        canonical_text(
            {
                "decision_id": decision_id,
                "kayit_zamani": kayit_zamani,
                "girdi_json": girdi_json,
                "cikti_json": cikti_json,
                "politika_surumu": politika_surumu,
                "politika_sha256": politika_sha256,
                "prev_hash": prev_hash,
            }
        )
    )


_COLS = (
    "seq, decision_id, kayit_zamani, girdi_json, cikti_json, politika_surumu, "
    "politika_sha256, prev_hash, row_hash"
)


def append(
    conn: Connection,
    *,
    girdi_json: str,
    cikti_json: str,
    politika_surumu: str,
    politika_sha256: str,
    decision_id: str | None = None,
    kayit_zamani: str | None = None,
) -> LogRow:
    """Append one record inside the caller's transaction (holds the advisory lock until it ends)."""
    conn.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": ADVISORY_LOCK_KEY})
    last = conn.execute(text("SELECT row_hash FROM decision_log ORDER BY seq DESC LIMIT 1"))
    prev = last.scalar() or GENESIS_HASH
    fields = {
        "decision_id": decision_id or str(uuid.uuid4()),
        "kayit_zamani": kayit_zamani or utc_now_text(),
        "girdi_json": girdi_json,
        "cikti_json": cikti_json,
        "politika_surumu": politika_surumu,
        "politika_sha256": politika_sha256,
        "prev_hash": prev,
    }
    fields["row_hash"] = compute_row_hash(**fields)
    row = conn.execute(
        text(
            "INSERT INTO decision_log (decision_id, kayit_zamani, girdi_json, cikti_json, "
            "politika_surumu, politika_sha256, prev_hash, row_hash) VALUES "
            "(:decision_id, :kayit_zamani, :girdi_json, :cikti_json, :politika_surumu, "
            f":politika_sha256, :prev_hash, :row_hash) RETURNING {_COLS}"
        ),
        fields,
    ).one()
    return LogRow(*row)


def record_decision(
    engine: Engine,
    girdi: DecisionInput,
    politika: Policy,
    politika_sha256: str,
    *,
    now: Callable[[], str] = utc_now_text,
) -> tuple[LogRow, InternalDecision]:
    """decide() is pure; the record layer adds time/id and persists canonical text."""
    karar = decide(girdi, politika)
    with engine.begin() as conn:
        row = append(
            conn,
            girdi_json=model_canonical_text(girdi),
            cikti_json=model_canonical_text(karar),
            politika_surumu=politika.surum,
            politika_sha256=politika_sha256,
            kayit_zamani=now(),
        )
    return row, karar


def read_all(conn: Connection) -> list[LogRow]:
    rows = conn.execute(text(f"SELECT {_COLS} FROM decision_log ORDER BY seq")).all()
    return [LogRow(*r) for r in rows]


def read_one(conn: Connection, decision_id: str) -> LogRow | None:
    r = conn.execute(
        text(f"SELECT {_COLS} FROM decision_log WHERE decision_id = :d"), {"d": decision_id}
    ).first()
    return LogRow(*r) if r else None


def verify_chain(conn: Connection) -> int:
    """Recompute every hash and link; also require stored texts to be canonical. Returns count."""
    prev = GENESIS_HASH
    rows = read_all(conn)
    for r in rows:
        if r.prev_hash != prev:
            raise ChainBroken(f"seq {r.seq}: prev_hash does not match previous row_hash")
        expected = compute_row_hash(
            decision_id=r.decision_id,
            kayit_zamani=r.kayit_zamani,
            girdi_json=r.girdi_json,
            cikti_json=r.cikti_json,
            politika_surumu=r.politika_surumu,
            politika_sha256=r.politika_sha256,
            prev_hash=r.prev_hash,
        )
        if expected != r.row_hash:
            raise ChainBroken(f"seq {r.seq}: row_hash mismatch")
        for t in (r.girdi_json, r.cikti_json):
            if canonical_text(json.loads(t)) != t:
                raise ChainBroken(f"seq {r.seq}: stored text is not canonical")
        prev = r.row_hash
    return len(rows)
