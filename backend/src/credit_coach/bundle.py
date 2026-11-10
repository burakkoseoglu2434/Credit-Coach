"""Bundle lock: SHA-256 of every frozen artifact. CI fails when any hash drifts.

Usage: python -m credit_coach.bundle write | verify
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from credit_coach.features import MANIFEST_PATH

ROOT = MANIFEST_PATH.parents[1]
LOCK_PATH = ROOT / "bundle.lock.json"
FILES = {
    "model": "bundle/pd_monotone.json",
    "calibrator_data": "bundle/calibration_data.npz",
    "features_manifest": "configs/features.yaml",
    "split": "configs/split.yaml",
    "monotone": "configs/monotone.yaml",
    "cost_and_thresholds": "configs/cost.yaml",
    "decision": "configs/decision.yaml",
    "policy_v1": "configs/policy/v1.yaml",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_lock(files: dict[str, str] = FILES, root: Path = ROOT) -> dict:
    return {
        "version": 1,
        "files": {k: {"path": v, "sha256": sha256(root / v)} for k, v in files.items()},
    }


def verify_lock(lock: dict, root: Path = ROOT) -> list[str]:
    """Return human-readable mismatches (empty list = bundle intact)."""
    problems = []
    for name, entry in lock["files"].items():
        path = root / entry["path"]
        if not path.exists():
            problems.append(f"{name}: missing {entry['path']}")
        elif sha256(path) != entry["sha256"]:
            problems.append(f"{name}: hash changed ({entry['path']})")
    return problems


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "verify"
    if cmd == "write":
        LOCK_PATH.write_text(json.dumps(build_lock(), indent=2, sort_keys=True) + "\n")
        print(f"wrote {LOCK_PATH}")
        return 0
    if cmd == "verify":
        problems = verify_lock(json.loads(LOCK_PATH.read_text()))
        for p in problems:
            print("BUNDLE MISMATCH:", p)
        return 1 if problems else 0
    print("usage: write | verify")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
