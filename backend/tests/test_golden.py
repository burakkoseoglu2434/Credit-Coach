"""Golden set v1 snapshot. Self-contained: no model, calibrator or raw data is loaded here
(except the optional selection-reproduction test, which skips when raw data is absent)."""

import json
import shutil

import pytest

from credit_coach import golden
from credit_coach.bundle import sha256 as file_sha256
from credit_coach.canonical import sha256_hex
from credit_coach.contract import parse_input
from credit_coach.features import allowed_features
from credit_coach.policy import POLICY_DIR

D = golden.GOLDEN_DIR


def _manifest():
    return json.loads((D / "MANIFEST.json").read_text())


def test_golden_is_bound_to_frozen_policy_v1_and_to_its_own_files():
    m = _manifest()
    assert m["policy_v1_sha256"] == file_sha256(POLICY_DIR / "v1.yaml"), (
        "policy v1 changed: v1 is frozen, create golden v2 instead of editing v1"
    )
    for name, h in m["files"].items():
        assert sha256_hex((D / name).read_bytes()) == h, f"{name} was edited outside `update`"


def test_snapshot_matches_byte_for_byte():
    diffs = golden.diff_against_snapshot()
    assert not diffs, "decision output changed:\n" + "\n".join(diffs[:20])


def test_inputs_are_self_contained_valid_and_model_free():
    for name in ("inputs_v1.jsonl", "variants_inputs.jsonl"):
        for rec in golden._lines(D / name):
            girdi = parse_input(rec["girdi"])
            assert set(rec["girdi"]["basvuru"]) == set(allowed_features())
            assert girdi.politika_surumu == "v1"


def test_variant_records_are_separate_and_labelled():
    v1_ids = {r["id"] for r in golden._lines(D / "inputs_v1.jsonl")}
    variants = golden._lines(D / "variants_inputs.jsonl")
    assert variants and all(r["label"].startswith("VARIANT:") and "politika" in r for r in variants)
    assert not v1_ids & {r["id"] for r in variants}
    assert all("politika" not in r for r in golden._lines(D / "inputs_v1.jsonl"))


def test_v1_expected_never_contains_rules_v1_cannot_fire_but_variants_do():
    v1_rules = {
        r for x in golden._lines(D / "expected_v1.jsonl") for r in x["cikti"]["tetiklenen_kurallar"]
    }
    var_rules = {
        r
        for x in golden._lines(D / "variants_expected.jsonl")
        for r in x["cikti"]["tetiklenen_kurallar"]
    }
    assert not v1_rules & {"R1_HARD_REJECT", "R3_WEAK_SUPPORT_NEAR"}
    assert {"R1_HARD_REJECT", "R3_WEAK_SUPPORT_NEAR"} <= var_rules


def test_real_records_come_only_from_calibration_ids_and_cover_strata():
    real = [r for r in golden._lines(D / "inputs_v1.jsonl") if r["id"].startswith("cal-")]
    strata = {s for r in real for s in r["strata"]}
    assert {"extreme_low", "extreme_high", "near_threshold_3band", "weak_support_zone"} <= strata
    assert {f"score_decile_{d}" for d in range(10)} <= strata


def test_update_flow_is_deliberate(tmp_path):
    for p in D.iterdir():
        shutil.copy(p, tmp_path / p.name)
    lines = (tmp_path / "expected_v1.jsonl").read_text().splitlines()
    rec = json.loads(lines[0])
    rec["cikti"]["dis_durum"] = (
        "REJECTED" if rec["cikti"]["dis_durum"] != "REJECTED" else "APPROVED"
    )
    lines[0] = golden.canonical_text(rec)
    (tmp_path / "expected_v1.jsonl").write_text("".join(x + "\n" for x in lines))
    before = (tmp_path / "expected_v1.jsonl").read_text()

    assert golden.diff_against_snapshot(tmp_path)  # drift is visible
    assert golden.update(tmp_path, accept_diff=False, reason="x") == 1  # flag required
    assert golden.update(tmp_path, accept_diff=True, reason="  ") == 1  # reason required
    assert (tmp_path / "expected_v1.jsonl").read_text() == before  # nothing written so far
    assert golden.update(tmp_path, accept_diff=True, reason="test of the flow") == 0
    assert not golden.diff_against_snapshot(tmp_path)
    assert "Intentional because: test of the flow" in (tmp_path / "CHANGELOG.md").read_text()
    assert (tmp_path / "expected_v1.jsonl").read_bytes() == (D / "expected_v1.jsonl").read_bytes()


def test_selection_is_reproducible_from_raw_data(tmp_path):
    from credit_coach.baseline import CSV

    if not CSV.exists():
        pytest.skip("raw data not available locally")
    golden.generate(tmp_path)
    for name in ("inputs_v1.jsonl", "variants_inputs.jsonl"):
        assert (tmp_path / name).read_bytes() == (D / name).read_bytes()
