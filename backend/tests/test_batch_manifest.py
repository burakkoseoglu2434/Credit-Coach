"""The batch path must not re-read the feature manifest (or any YAML) per row."""

import pathlib
import time

import pandas as pd
import yaml

from credit_coach.decision_scenarios import in_support_basvuru
from credit_coach.features import allowed_features
from credit_coach.policy import load_policy
from credit_coach.recourse import hazirla, load_demo_catalog, sec_from_scores
from credit_coach.recourse_report import vektorler
from credit_coach.recourse_scorers import SyntheticScorer
from credit_coach.support import load_support

N = 10_000


def frame(n: int) -> pd.DataFrame:
    row = in_support_basvuru(load_support())
    return pd.DataFrame([row] * n)[allowed_features()]


class Counter:
    def __init__(self, monkeypatch) -> None:
        self.reads = 0  # file reads
        self.parses = 0  # yaml parses
        orig_read, orig_load = pathlib.Path.read_text, yaml.safe_load

        def read(p, *a, **k):
            self.reads += 1
            return orig_read(p, *a, **k)

        def load(*a, **k):
            self.parses += 1
            return orig_load(*a, **k)

        monkeypatch.setattr(pathlib.Path, "read_text", read)
        monkeypatch.setattr(yaml, "safe_load", load)


def test_conversion_reads_manifest_a_constant_number_of_times(monkeypatch):
    small, big = frame(100), frame(N)
    c = Counter(monkeypatch)
    vektorler(small)
    reads_small, parses_small = c.reads, c.parses
    c.reads = c.parses = 0
    t = time.perf_counter()
    out = vektorler(big)
    elapsed = time.perf_counter() - t
    assert len(out) == N
    assert (c.reads, c.parses) == (reads_small, parses_small)  # independent of the row count
    assert reads_small <= 2  # the manifest is read per call (twice at most), never per row
    assert elapsed < 10.0, elapsed


def test_conversion_matches_golden_cleaning():
    from credit_coach.features import load_manifest
    from credit_coach.golden import _basvuru

    df = frame(25)
    df.loc[3, "dti"] = float("nan")
    kinds = {c.ad: c.tip for c in load_manifest()}
    expected = [_basvuru(r, kinds) for r in df.to_dict("records")]
    assert vektorler(df) == expected


def test_search_and_selection_read_no_files_per_row(monkeypatch):
    pol, sup, kat, sc = load_policy("v1"), load_support(), load_demo_catalog(), SyntheticScorer()
    recs = vektorler(frame(300))
    c = Counter(monkeypatch)
    for b in recs:
        hz = hazirla(b, kat)
        skorlar = sc.skorla_toplu([b] + [a.vektor for a in hz[1]])
        sec_from_scores(b, hz, skorlar[0], skorlar[1:], pol, sup, kat, 0.02)
    assert c.reads == 0


def test_golden_basvuru_reads_manifest_per_row_known_defect(monkeypatch):
    """Documents the defect found in week 4: golden._basvuru calls allowed_features() (which
    re-parses the YAML manifest) for every row. Not carried into the batch path. If golden.py is
    fixed later, update this test."""
    from credit_coach.features import load_manifest
    from credit_coach.golden import _basvuru

    df, kinds = frame(20), {c.ad: c.tip for c in load_manifest()}
    c = Counter(monkeypatch)
    for r in df.to_dict("records"):
        _basvuru(r, kinds)
    assert c.reads >= 20
