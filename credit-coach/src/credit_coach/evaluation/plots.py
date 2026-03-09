from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_acceptance_frontier(plans_df: pd.DataFrame, out_path: str | Path) -> Path:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(7, 5))
    x = plans_df.get("cost", pd.Series([0] * len(plans_df)))
    y = plans_df.get("risk_margin", pd.Series([0] * len(plans_df)))
    c = plans_df.get("status", pd.Series(["PENDING"] * len(plans_df)))
    colors = c.map({"APPROVED": "green", "NEEDS_REVIEW": "orange", "REJECTED": "red"}).fillna("gray")
    ax.scatter(x, y, c=colors)
    ax.set_xlabel("Cost")
    ax.set_ylabel("Risk margin")
    ax.set_title("Acceptance Frontier")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out
