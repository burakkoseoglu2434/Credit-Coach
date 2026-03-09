from __future__ import annotations

import json
from pathlib import Path


def load_graph(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Graph file not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def get_parents(graph: dict, node: str) -> list[str]:
    return [e["source"] for e in graph.get("edges", []) if e["target"] == node]


def get_children(graph: dict, node: str) -> list[str]:
    return [e["target"] for e in graph.get("edges", []) if e["source"] == node]
