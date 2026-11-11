"""External data sources recorded in configs/data_source.yaml (path + SHA-256, never copied).

Usage: python -m credit_coach.data_source verify   (hashes the files; reads ~2 GB)
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import yaml

from credit_coach.features import MANIFEST_PATH

ROOT = MANIFEST_PATH.parents[1]
SOURCE_PATH = ROOT / "configs" / "data_source.yaml"
ENV_REJECTED = "CREDIT_COACH_REJECTED_LC"


def load_sources(path: Path = SOURCE_PATH) -> dict:
    return yaml.safe_load(path.read_text())


def rejected_path(sources: dict | None = None) -> Path:
    env = os.environ.get(ENV_REJECTED)
    return Path(env) if env else Path((sources or load_sources())["lc_reddedilen"]["yol"])


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify(sources: dict | None = None) -> list[str]:
    """Return problems (empty = every recorded file exists with the recorded hash)."""
    src = sources or load_sources()
    entry = src["lc_reddedilen"]
    pairs = [
        (rejected_path(src), entry["sha256"]),
        (Path(entry["yan_dosya_accepted"]["yol"]), entry["yan_dosya_accepted"]["sha256"]),
    ]
    problems = []
    for p, want in pairs:
        if not p.exists():
            problems.append(f"yok: {p}")
        elif file_sha256(p) != want:
            problems.append(f"hash farklı: {p}")
    return problems


def main() -> int:
    problems = verify()
    print("\n".join(problems) if problems else "tamam: yol ve hash eşleşiyor")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
