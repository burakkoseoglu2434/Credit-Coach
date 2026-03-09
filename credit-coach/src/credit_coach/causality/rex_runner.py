from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def run_rex_adapter(
    df: pd.DataFrame,
    feature_cols: list[str],
    min_edge_weight: float = 0.1,
    algorithm: str = "pc",
    output_path: str | Path = "artifacts/models/causal_graph.json",
) -> dict:
    corr = df[feature_cols].corr(numeric_only=True).fillna(0.0)
    edges: list[dict] = []

    for i, src in enumerate(feature_cols):
        for j, dst in enumerate(feature_cols):
            if i >= j:
                continue
            w = float(abs(corr.loc[src, dst]))
            if w < min_edge_weight:
                continue
            edges.append({"source": src, "target": dst, "weight": w})

    graph = {
        "algorithm": algorithm,
        "nodes": feature_cols,
        "edges": edges,
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    return graph
