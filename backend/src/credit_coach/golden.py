"""Golden set v1 (week 3.5): frozen decision inputs + expected outputs, a regression snapshot.

generate  select ~200 real calibration-split applications ONCE (seed 42), freeze inputs, write
          expected outputs. Needs the raw CSV, the model and the calibrator; refuses to overwrite.
check     re-run decide() on the frozen inputs, show the diff against the snapshot (exit 1 on diff).
update    accept a diff on purpose: needs --accept-diff and --reason; appends to CHANGELOG.md.

The tests never touch the model, the calibrator or raw data: inputs are frozen in the files.
This is a REGRESSION test ("did the code change?"), not proof that decisions are right.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from credit_coach.bundle import ROOT
from credit_coach.bundle import sha256 as file_sha256
from credit_coach.canonical import canonical_text, model_canonical_text, sha256_hex
from credit_coach.contract import parse_input
from credit_coach.decision_engine import decide
from credit_coach.decision_scenarios import policy_variant, sample_basvuru, scenarios
from credit_coach.policy import POLICY_DIR, Policy, load_policy

GOLDEN_DIR = ROOT / "tests" / "golden"
SEED = 42
FILES = ("inputs_v1.jsonl", "expected_v1.jsonl", "variants_inputs.jsonl", "variants_expected.jsonl")


# ---------------------------------------------------------------- expected outputs (no raw data)


def _lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def policy_for(rec: dict, v1: Policy) -> Policy:
    return Policy(**rec["politika"]) if "politika" in rec else v1


def expected_line(rec: dict, v1: Policy) -> str:
    girdi = parse_input(rec["girdi"])
    out = json.loads(model_canonical_text(decide(girdi, policy_for(rec, v1))))
    return canonical_text({"id": rec["id"], "cikti": out})


def compute_expected(directory: Path = GOLDEN_DIR) -> dict[str, list[str]]:
    v1 = load_policy("v1")
    return {
        "expected_v1.jsonl": [expected_line(r, v1) for r in _lines(directory / "inputs_v1.jsonl")],
        "variants_expected.jsonl": [
            expected_line(r, v1) for r in _lines(directory / "variants_inputs.jsonl")
        ],
    }


def _write_lines(path: Path, lines: list[str]) -> None:
    path.write_text("".join(line + "\n" for line in lines))


def manifest_for(directory: Path = GOLDEN_DIR) -> dict:
    return {
        "golden_version": "v1",
        "policy_v1_sha256": file_sha256(POLICY_DIR / "v1.yaml"),
        "selection": {"seed": SEED, "source": "calibration split only", "rule": "see README.md"},
        "files": {f: sha256_hex((directory / f).read_bytes()) for f in FILES},
    }


def diff_against_snapshot(directory: Path = GOLDEN_DIR) -> list[str]:
    out = []
    for name, new in compute_expected(directory).items():
        old = (directory / name).read_text().splitlines()
        if len(old) != len(new):
            out.append(f"{name}: {len(old)} stored lines vs {len(new)} replayed")
            continue
        for a, b in zip(old, new, strict=True):
            if a != b:
                ja, jb = json.loads(a), json.loads(b)
                keys = sorted(
                    k
                    for k in set(ja["cikti"]) | set(jb["cikti"])
                    if ja["cikti"].get(k) != jb["cikti"].get(k)
                )
                out.append(
                    f"{name}: {ja['id']} fields {keys}: "
                    + "; ".join(
                        f"{k}: {ja['cikti'].get(k)!r} -> {jb['cikti'].get(k)!r}" for k in keys
                    )
                )
    return out


def update(directory: Path, *, accept_diff: bool, reason: str | None) -> int:
    diffs = diff_against_snapshot(directory)
    if not diffs:
        print("snapshot already matches; nothing to update")
        return 0
    print("\n".join(diffs))
    if not accept_diff or not (reason and reason.strip()):
        print("\nNOT written. Re-run with --accept-diff --reason '<why the change is intentional>'")
        return 1
    if (
        file_sha256(POLICY_DIR / "v1.yaml")
        != json.loads((directory / "MANIFEST.json").read_text())["policy_v1_sha256"]
    ):
        print("policy v1 changed: v1 is frozen. Create golden v2 instead of updating v1.")
        return 1
    for name, lines in compute_expected(directory).items():
        _write_lines(directory / name, lines)
    manifest = manifest_for(directory)
    (directory / "MANIFEST.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    with (directory / "CHANGELOG.md").open("a") as f:
        f.write(f"\n- {len(diffs)} changed line(s). Intentional because: {reason.strip()}\n")
    print("\nwritten; remember the commit message: 'change is intentional because ...'")
    return 0


# ---------------------------------------------------------------- generation (needs raw data)


def _clean(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    if isinstance(v, np.generic):
        v = v.item()
    return v


def _basvuru(row, kinds: dict[str, str]) -> dict:
    from credit_coach.features import allowed_features

    out = {}
    for name in allowed_features():
        v = _clean(row[name])
        if v is not None and kinds[name] == "int":
            v = int(v)
        elif v is not None and kinds[name] == "float":
            v = float(v)
        out[name] = v
    return out


def select_records() -> list[dict]:
    """Stratified, seeded selection from the calibration split. Deterministic given the bundle."""
    import pandas as pd
    from xgboost import XGBClassifier

    from credit_coach.baseline import CSV
    from credit_coach.calibration import fit_venn_abers, predict_interval
    from credit_coach.features import load_manifest
    from credit_coach.modeling import dev_frame, split_xy

    raw = pd.read_csv(CSV)
    dev = dev_frame(raw)
    _, _, X_ca, _ = split_xy(dev)
    ca = dev[dev["split"] == "calibration"]
    model = XGBClassifier()
    model.load_model(ROOT / "bundle" / "pd_monotone.json")
    s = model.predict_proba(X_ca)[:, 1]
    cal = np.load(ROOT / "bundle" / "calibration_data.npz")
    assert np.allclose(s, cal["scores"], atol=1e-6), "bundle scores differ from the frozen split"
    low, high, point = predict_interval(fit_venn_abers(cal["scores"], cal["labels"].astype(int)), s)

    v1 = load_policy("v1")
    thr, band = v1.onay_esigi, v1.band
    n = len(s)
    rng = np.random.default_rng(SEED)
    chosen: dict[int, list[str]] = {}

    def take(stratum: str, idx: np.ndarray, k: int | None) -> None:
        idx = np.array(sorted(i for i in idx if i not in chosen))
        if k is not None and len(idx) > k:
            idx = np.sort(rng.choice(idx, size=k, replace=False))
        for i in idx:
            chosen.setdefault(int(i), []).append(stratum)

    order = np.lexsort((np.arange(n), s))
    take("extreme_low", order[:10], None)
    take("extreme_high", order[-10:], None)
    take("near_threshold_3band", np.where(np.abs(point - thr) <= 3 * band)[0], 40)
    take("interval_straddles", np.where((low <= thr) & (thr <= high))[0], 30)
    weak = np.zeros(n, dtype=bool)
    for a, b in v1.zayif_destek_araliklari:
        weak |= (s >= a) & (s <= b)
    take("weak_support_zone", np.where(weak)[0], 30)
    for d, chunk in enumerate(np.array_split(order, 10)):
        take(f"score_decile_{d}", chunk, 10)

    kinds = {c.ad: c.tip for c in load_manifest()}
    recs = []
    for i in sorted(chosen):
        row = ca.iloc[i]
        recs.append(
            {
                "id": f"cal-{ca.index[i]}",
                "strata": chosen[i],
                "girdi": {
                    "basvuru": _basvuru(row, kinds),
                    "p_low": float(low[i]),
                    "p_point": float(point[i]),
                    "p_high": float(high[i]),
                    "ham_skor": float(s[i]),
                    "politika_surumu": "v1",
                    "plan_available": None,
                },
            }
        )
    return recs


def build_variants(real: list[dict], v1: Policy) -> list[dict]:
    thr = v1.onay_esigi
    recs = []
    for s in scenarios():
        if not s.policy_updates:
            continue
        girdi = {
            "basvuru": sample_basvuru(),
            "p_low": s.p[0],
            "p_point": s.p[1],
            "p_high": s.p[2],
            "ham_skor": s.ham_skor,
            "politika_surumu": "v1",
            "plan_available": s.plan_available,
        }
        pol = policy_variant(**dict(s.policy_updates))
        recs.append(
            {
                "id": f"variant-scenario-{s.name}",
                "label": "VARIANT:scenario",
                "girdi": girdi,
                "politika": pol.model_dump(mode="json"),
            }
        )
    by_p_low = sorted(real, key=lambda r: r["girdi"]["p_low"])[-15:]
    near = [r for r in real if "near_threshold_3band" in r["strata"]][:15]
    r1 = policy_variant(ret_esigi=0.30)
    r3 = policy_variant(zayif_destek_araliklari=((thr - 0.05, thr + 0.05),))
    for r in by_p_low:
        recs.append(
            {
                "id": f"variant-R1-{r['id']}",
                "label": "VARIANT:R1_ret_esigi_0.30",
                "girdi": r["girdi"],
                "politika": r1.model_dump(mode="json"),
            }
        )
    for r in near:
        recs.append(
            {
                "id": f"variant-R3-{r['id']}",
                "label": "VARIANT:R3_weak_zone_around_threshold",
                "girdi": r["girdi"],
                "politika": r3.model_dump(mode="json"),
            }
        )
    return recs


def generate(directory: Path = GOLDEN_DIR) -> None:
    if (directory / "inputs_v1.jsonl").exists():
        raise SystemExit("golden v1 inputs exist and are frozen; refusing to overwrite")
    directory.mkdir(parents=True, exist_ok=True)
    v1 = load_policy("v1")
    real = select_records()
    synthetic = [
        {
            "id": f"synthetic-{s.name}",
            "strata": ["synthetic_v1_scenario"],
            "girdi": {
                "basvuru": sample_basvuru(),
                "p_low": s.p[0],
                "p_point": s.p[1],
                "p_high": s.p[2],
                "ham_skor": s.ham_skor,
                "politika_surumu": "v1",
                "plan_available": s.plan_available,
            },
        }
        for s in scenarios()
        if not s.policy_updates
    ]
    _write_lines(directory / "inputs_v1.jsonl", [canonical_text(r) for r in real + synthetic])
    _write_lines(
        directory / "variants_inputs.jsonl", [canonical_text(r) for r in build_variants(real, v1)]
    )
    for name, lines in compute_expected(directory).items():
        _write_lines(directory / name, lines)
    (directory / "MANIFEST.json").write_text(
        json.dumps(manifest_for(directory), indent=1, sort_keys=True) + "\n"
    )


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else ""
    if cmd == "generate":
        generate()
        return 0
    if cmd == "check":
        diffs = diff_against_snapshot()
        print("\n".join(diffs) or "snapshot matches")
        return 1 if diffs else 0
    if cmd == "update":
        reason = argv[argv.index("--reason") + 1] if "--reason" in argv else None
        return update(GOLDEN_DIR, accept_diff="--accept-diff" in argv, reason=reason)
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
