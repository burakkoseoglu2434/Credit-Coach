"""Deterministically export the OpenAPI schema to a JSON file."""

import json
import sys
from pathlib import Path

from credit_coach.app import app


def main(out: str) -> None:
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../frontend/openapi.json")
