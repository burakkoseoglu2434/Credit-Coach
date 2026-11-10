"""Cohort definition, target and time-based split (ADR-002). No random splitting."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

SPLIT_CONFIG_PATH = Path(__file__).resolve().parents[3] / "configs" / "split.yaml"
ORDER = ("train", "calibration", "test")


@dataclass(frozen=True)
class Window:
    start: date
    end: date


@dataclass(frozen=True)
class SplitConfig:
    term: str
    issue_d_min: date
    issue_d_max: date
    min_gap_months: int
    splits: dict[str, Window]


def _months_between(a: date, b: date) -> int:
    return (b.year - a.year) * 12 + (b.month - a.month)


def load_split_config(path: Path = SPLIT_CONFIG_PATH) -> SplitConfig:
    raw = yaml.safe_load(path.read_text())
    cfg = SplitConfig(
        term=raw["cohort"]["term"],
        issue_d_min=raw["cohort"]["issue_d_min"],
        issue_d_max=raw["cohort"]["issue_d_max"],
        min_gap_months=raw["min_gap_months"],
        splits={k: Window(**v) for k, v in raw["splits"].items()},
    )
    validate_config(cfg)
    return cfg


def validate_config(cfg: SplitConfig) -> None:
    if tuple(cfg.splits) != ORDER:
        raise ValueError(f"splits must be exactly {ORDER} in order")
    prev_end = None
    for name in ORDER:
        w = cfg.splits[name]
        if w.start > w.end:
            raise ValueError(f"{name}: start after end")
        if w.start < cfg.issue_d_min or w.end > cfg.issue_d_max:
            raise ValueError(f"{name}: outside cohort range")
        if prev_end is not None and _months_between(prev_end, w.start) <= cfg.min_gap_months:
            raise ValueError(f"{name}: gap to previous split below {cfg.min_gap_months} months")
        prev_end = w.end


def parse_issue_d(s: pd.Series) -> pd.Series:
    """'Dec-2015' -> Timestamp (first of month)."""
    return pd.to_datetime(s, format="%b-%Y")


def cohort(df: pd.DataFrame, cfg: SplitConfig | None = None) -> pd.DataFrame:
    """Mature-cohort filter. Adds a parsed `issue_date` column."""
    cfg = cfg or load_split_config()
    d = parse_issue_d(df["issue_d"])
    mask = (
        (df["term"].str.strip() == cfg.term)
        & (d >= pd.Timestamp(cfg.issue_d_min))
        & (d <= pd.Timestamp(cfg.issue_d_max))
    )
    return df.loc[mask].assign(issue_date=d[mask])


def build_target(df: pd.DataFrame) -> pd.Series:
    """Target is the existing binary `target` (1 = bad outcome); must be 0/1, no nulls."""
    y = df["target"]
    if y.isna().any() or not set(y.unique()) <= {0, 1}:
        raise ValueError("target must be binary 0/1 without nulls")
    return y.astype(int)


def assign_split(df: pd.DataFrame, cfg: SplitConfig | None = None) -> pd.Series:
    """Label each cohort row train/calibration/test, or 'gap' if it falls between windows."""
    cfg = cfg or load_split_config()
    c = cohort(df, cfg)
    label = pd.Series("gap", index=c.index, dtype="object")
    for name in ORDER:
        w = cfg.splits[name]
        label[
            (c["issue_date"] >= pd.Timestamp(w.start)) & (c["issue_date"] <= pd.Timestamp(w.end))
        ] = name
    return label


def split_report(df: pd.DataFrame, cfg: SplitConfig | None = None) -> pd.DataFrame:
    """Row count and bad rate per split (and gap)."""
    cfg = cfg or load_split_config()
    c = cohort(df, cfg)
    label = assign_split(df, cfg)
    y = build_target(c)
    out = y.groupby(label).agg(rows="size", bad_rate="mean")
    return out.reindex([*ORDER, "gap"]).fillna(0)
