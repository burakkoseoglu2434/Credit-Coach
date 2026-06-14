from __future__ import annotations

import argparse
from pathlib import Path

from credit_coach.evaluation.coverage_diagnostics import DEFAULT_GAP_CLOSURE_EPSILON, write_coverage_diagnostics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit additive coverage diagnostic artifacts for a cohort evaluation run directory.",
    )
    parser.add_argument(
        "--run_dir",
        type=str,
        required=True,
        help="Evaluation run directory containing customer_level_analysis.csv",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="",
        help="Optional output directory. Default: <run_dir>/coverage_diagnostics",
    )
    parser.add_argument(
        "--gap_closure_epsilon",
        type=float,
        default=DEFAULT_GAP_CLOSURE_EPSILON,
        help="Epsilon threshold for non-trivial gap-closure signal (default: 0.05).",
    )
    return parser.parse_args()


def run(args: argparse.Namespace) -> Path:
    run_dir = Path(args.run_dir).resolve()
    customer_csv = run_dir / "customer_level_analysis.csv"
    if not customer_csv.is_file():
        raise FileNotFoundError(f"Missing customer_level_analysis.csv: {customer_csv}")

    output_dir = Path(args.output_dir).resolve() if args.output_dir else (run_dir / "coverage_diagnostics")
    paths = write_coverage_diagnostics(
        customer_csv_path=customer_csv,
        output_dir=output_dir,
        gap_closure_epsilon=float(args.gap_closure_epsilon),
    )
    return paths.output_dir


def main() -> None:
    output_dir = run(parse_args())
    print(str(output_dir))


if __name__ == "__main__":
    main()

