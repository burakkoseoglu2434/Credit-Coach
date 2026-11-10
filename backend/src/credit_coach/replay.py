"""Replay (week 3.4): re-run decide() on logged inputs and compare the decision byte for byte.

What replay reproduces: the DECISION layer only. The log stores p_low/p_point/p_high/ham_skor as
inputs, so replay re-runs decide() with the policy named in the record, not the model.
Score-layer reproducibility (features -> p_point) needs a separate check and is NOT covered here.

Order: verify_chain first (a broken chain stops everything), then per record:
policy file hash vs the record's politika_sha256 (mismatch = hard error, no guessing), then
decision comparison on cikti_json only. row_hash, timestamp and decision_id are not reproducible
and are excluded. The bundle hash is reported separately: a changed bundle is information, not
an error. Runs with read-only (SELECT) access.

Usage: python -m credit_coach.replay --all | --id <decision_id>
Exit codes: 0 all match, 1 differences or errors, 2 chain broken.
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import Connection, create_engine

from credit_coach.bundle import sha256 as file_sha256
from credit_coach.canonical import model_canonical_text
from credit_coach.contract import InvalidDecisionInput, parse_input
from credit_coach.decision_engine import decide
from credit_coach.decision_log import (
    ChainBroken,
    LogRow,
    current_bundle_sha256,
    read_all,
    read_one,
    verify_chain,
)
from credit_coach.policy import POLICY_DIR, Policy, UnknownPolicyVersion, load_policy

PolicyLoader = Callable[[str], tuple[Policy, str]]


def default_loader(policy_dir: Path = POLICY_DIR) -> PolicyLoader:
    def load(surum: str) -> tuple[Policy, str]:
        policy = load_policy(surum, policy_dir)
        return policy, file_sha256(policy_dir / f"{surum}.yaml")

    return load


@dataclass(frozen=True)
class Difference:
    seq: int
    decision_id: str
    field: str
    stored: object
    replayed: object


@dataclass(frozen=True)
class ReplayError:
    seq: int
    decision_id: str
    kind: str  # POLICY_UNKNOWN | POLICY_FILE_HASH_MISMATCH | INPUT_INVALID
    detail: str


@dataclass
class ReplayReport:
    chain_ok: bool = False
    chain_error: str | None = None
    checked: int = 0
    matched: int = 0
    differences: list[Difference] = field(default_factory=list)
    errors: list[ReplayError] = field(default_factory=list)
    bundle_notes: list[str] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        if not self.chain_ok:
            return 2
        return 0 if not self.differences and not self.errors else 1

    def render(self) -> str:
        lines = [
            "Replay kapsamı: karar katmanı (decide). Skor katmanı bu raporda YOK.",
            f"Zincir: {'tamam' if self.chain_ok else 'BOZUK: ' + str(self.chain_error)}",
            f"Kontrol edilen: {self.checked}, eşleşen: {self.matched}",
        ]
        lines += [f"Bundle notu: {n}" for n in self.bundle_notes]
        lines += [
            f"FARK seq={d.seq} id={d.decision_id} alan={d.field} kayıt={d.stored!r} "
            f"yeniden={d.replayed!r}"
            for d in self.differences
        ]
        lines += [f"HATA seq={e.seq} id={e.decision_id} {e.kind}: {e.detail}" for e in self.errors]
        return "\n".join(lines)


def _field_diffs(row: LogRow, replayed_text: str) -> list[Difference]:
    stored, again = json.loads(row.cikti_json), json.loads(replayed_text)
    keys = sorted(set(stored) | set(again))
    diffs = [
        Difference(row.seq, row.decision_id, k, stored.get(k), again.get(k))
        for k in keys
        if stored.get(k) != again.get(k)
    ]
    return diffs or [Difference(row.seq, row.decision_id, "(bytes)", row.cikti_json, replayed_text)]


def replay_rows(rows: list[LogRow], loader: PolicyLoader, report: ReplayReport) -> None:
    cache: dict[str, tuple[Policy, str] | ReplayError | None] = {}
    now_bundle = current_bundle_sha256()
    seen_bundles: set[str] = set()
    for row in rows:
        report.checked += 1
        if row.bundle_sha256 not in seen_bundles:
            seen_bundles.add(row.bundle_sha256)
            same = "aynı" if row.bundle_sha256 == now_bundle else "FARKLI"
            report.bundle_notes.append(
                f"kayıttaki bundle {row.bundle_sha256[:12]}, mevcut {now_bundle[:12]} ({same})"
            )
        try:
            policy, file_hash = loader(row.politika_surumu)
        except UnknownPolicyVersion as e:
            report.errors.append(ReplayError(row.seq, row.decision_id, "POLICY_UNKNOWN", str(e)))
            continue
        if file_hash != row.politika_sha256:
            report.errors.append(
                ReplayError(
                    row.seq,
                    row.decision_id,
                    "POLICY_FILE_HASH_MISMATCH",
                    f"record {row.politika_sha256[:12]} != file {file_hash[:12]} "
                    f"({row.politika_surumu})",
                )
            )
            continue
        cache[row.politika_surumu] = (policy, file_hash)
        try:
            girdi = parse_input(json.loads(row.girdi_json))
            replayed = model_canonical_text(decide(girdi, policy))
        except (InvalidDecisionInput, ValueError) as e:
            report.errors.append(ReplayError(row.seq, row.decision_id, "INPUT_INVALID", str(e)))
            continue
        if replayed == row.cikti_json:
            report.matched += 1
        else:
            report.differences += _field_diffs(row, replayed)


def replay(
    conn: Connection,
    *,
    decision_id: str | None = None,
    loader: PolicyLoader | None = None,
) -> ReplayReport:
    report = ReplayReport()
    try:
        verify_chain(conn)
        report.chain_ok = True
    except ChainBroken as e:
        report.chain_error = str(e)
        return report
    if decision_id is None:
        rows = read_all(conn)
    else:
        one = read_one(conn, decision_id)
        rows = [one] if one else []
    replay_rows(rows, loader or default_loader(), report)
    return report


def main(argv: list[str]) -> int:
    url = os.environ.get("CREDIT_COACH_APP_DB_URL")
    if not url:
        print("CREDIT_COACH_APP_DB_URL (cc_app, SELECT) is required", file=sys.stderr)
        return 1
    one = argv[argv.index("--id") + 1] if "--id" in argv else None
    if "--all" not in argv and one is None:
        print(__doc__)
        return 1
    with create_engine(url).connect() as conn:
        report = replay(conn, decision_id=one)
    print(report.render())
    return report.exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
