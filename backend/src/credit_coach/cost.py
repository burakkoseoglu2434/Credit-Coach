"""Cost assumptions for the approval threshold, derived from the TRAIN window only.

The columns used here (funded_amnt, total_rec_prncp, total_rec_int, recoveries, loan_status) are
post-origination outcomes. They are NOT model inputs and never enter a training matrix.
They are read through a separate loader straight from the raw LendingClub file.
"""

from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd

from credit_coach.split import SplitConfig, load_split_config

COST_COLUMNS = (
    "funded_amnt",
    "total_rec_prncp",
    "total_rec_int",
    "recoveries",
    "loan_status",
)
GOOD = ("Fully Paid",)
BAD = ("Charged Off", "Default")
LABEL = "varsayım: eğitim diliminden ampirik, vade ve fon maliyeti dahil değil"


def load_train_outcomes(raw_csv: str, cfg: SplitConfig | None = None) -> pd.DataFrame:
    """Resolved loans in the TRAIN window (term + issue_d from split.yaml). No other months."""
    cfg = cfg or load_split_config()
    w = cfg.splits["train"]
    sql = f"""
        SELECT TRY_CAST(funded_amnt AS DOUBLE) AS funded_amnt,
               TRY_CAST(total_rec_prncp AS DOUBLE) AS total_rec_prncp,
               TRY_CAST(total_rec_int AS DOUBLE) AS total_rec_int,
               TRY_CAST(recoveries AS DOUBLE) AS recoveries,
               loan_status
        FROM read_csv('{raw_csv}', header=true, all_varchar=true, ignore_errors=true)
        WHERE trim(term) = '{cfg.term}'
          AND TRY_STRPTIME(issue_d, '%b-%Y') >= DATE '{w.start}'
          AND TRY_STRPTIME(issue_d, '%b-%Y') <= DATE '{w.end}'
          AND loan_status IN ({", ".join(repr(s) for s in (*GOOD, *BAD))})
    """
    return duckdb.sql(sql).df()


def _summ(x: pd.Series) -> dict[str, float]:
    return {"mean": float(x.mean()), "median": float(x.median()), "n": int(len(x))}


def cost_stats(df: pd.DataFrame) -> dict:
    """LGD, good-loan yield, interest collected on defaults, and default net loss."""
    bad = df[df["loan_status"].isin(BAD)]
    good = df[df["loan_status"].isin(GOOD)]
    lgd = (bad["funded_amnt"] - bad["total_rec_prncp"] - bad["recoveries"]) / bad["funded_amnt"]
    yield_good = good["total_rec_int"] / good["funded_amnt"]
    int_bad = bad["total_rec_int"] / bad["funded_amnt"]
    net_loss = lgd - int_bad
    return {
        "lgd": _summ(lgd),
        "yield_good": _summ(yield_good),
        "interest_on_defaults": _summ(int_bad),
        "default_net_loss": _summ(net_loss),
        "bad_rate": float(len(bad) / len(df)),
        "n_resolved": int(len(df)),
    }


def break_even_pd(gain: float, loss: float) -> float:
    """Approve while PD <= gain / (gain + loss): p * loss = (1 - p) * gain."""
    if gain <= 0 or loss <= 0:
        raise ValueError("gain and loss must be positive")
    return gain / (gain + loss)


def sensitivity(gain: float, loss: float, rel: float = 0.2) -> pd.DataFrame:
    """Break-even PD for loss x (1 -/+ rel) by gain x (1 -/+ rel)."""
    f = (1 - rel, 1.0, 1 + rel)
    return pd.DataFrame(
        {f"gain x{g:.1f}": [break_even_pd(gain * g, loss * l_) for l_ in f] for g in f},
        index=[f"loss x{l_:.1f}" for l_ in f],
    )


def clean(x):
    if isinstance(x, dict):
        return {k: clean(v) for k, v in x.items()}
    return float(x) if isinstance(x, (np.floating, float)) else x
