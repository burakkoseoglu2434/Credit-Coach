---
phase: 71-coverage-diagnostics-failure-analysis
plan: "01"
subsystem: evaluation
tags: [coverage, diagnostics, pandas, cli]
requires: []
provides:
  - "Deterministic coverage-loss bucketing from customer_level_analysis.csv"
  - "Post-hoc CLI to emit coverage_diagnostics/* artifacts per run directory"
  - "Opt-in cohort-eval emission hook for coverage diagnostics (additive only)"
affects: [phase-72, phase-73, cohort-evaluation, artifacts]
tech-stack:
  added: []
  patterns: ["Additive diagnostics emitted alongside existing evaluation artifacts"]
key-files:
  created:
    - credit-coach/src/credit_coach/evaluation/coverage_diagnostics.py
    - credit-coach/src/credit_coach/cli/run_v27_coverage_diagnostics.py
    - credit-coach/tests/test_coverage_diagnostics.py
  modified:
    - credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py
key-decisions:
  - "Keep Phase 71 diagnostic-only by making cohort-eval emission opt-in via --emit_coverage_diagnostics."
  - "Normalize segments by mapping recoverability_bucket structural_limited -> hard_denied for roadmap-aligned reporting."
  - "Use explicit, reproducible thresholds (gap_closure_epsilon=0.05) and categorical movement_potential to avoid brittle numeric assumptions."
patterns-established:
  - "coverage_diagnostics/ artifact family is additive and idempotent per run_dir"
requirements-completed: [COV-01]
duration: 45min
completed: 2026-04-18
---

# Phase 71: Coverage Diagnostics & Failure Analysis — Plan 01 Summary

**Coverage diagnostics library + CLI now emit additive, per-customer coverage-loss buckets and summary artifacts from `customer_level_analysis.csv`.**

## Performance

- **Duration:** 45 min
- **Tasks:** 4
- **Files modified:** 4

## Accomplishments
- Implemented `credit_coach.evaluation.coverage_diagnostics` to produce deterministic derived buckets and summary outputs.
- Added `python -m credit_coach.cli.run_v27_coverage_diagnostics` for post-hoc diagnostics on any evaluation run directory.
- Added opt-in diagnostics emission hook to the cohort evaluation runner (`--emit_coverage_diagnostics`) without changing selection/gating semantics.
- Added unit tests covering bucket assignment and required artifact emission.

## Task Commits

Each task was committed atomically:

1. **Task 1: Coverage diagnostics library** — `4894e01` (feat)
2. **Task 2: Post-hoc diagnostics CLI** — `a2cb704` (feat)
3. **Task 3: Opt-in cohort-eval emission hook** — `257e63d` (feat)
4. **Task 4: Coverage diagnostics tests** — `9be8d96` (test)

**Plan metadata:** pending (docs: summary)

## Files Created/Modified
- `credit-coach/src/credit_coach/evaluation/coverage_diagnostics.py` — derived taxonomy + writers for `coverage_diagnostics/*`
- `credit-coach/src/credit_coach/cli/run_v27_coverage_diagnostics.py` — post-hoc CLI wrapper calling the library entrypoint
- `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py` — `--emit_coverage_diagnostics` (default off) additive emission hook
- `credit-coach/tests/test_coverage_diagnostics.py` — bucket + artifact emission tests

## Decisions Made
- Kept diagnostics emission opt-in to preserve Phase 71 “diagnostic-only” guardrail (additive outputs, no default behavior change).
- Emitted explicit mode outcome fields in the per-customer breakdown (`recourse_mode`, `recommendation_mode`, `selected_recommendation_source`, empty/zero-action flags).

## Deviations from Plan

None — executed as written.

## Issues Encountered
- `tests/test_cohort_evaluation.py` constructs `SimpleNamespace` args; adding a new CLI flag required guarding via `getattr(args, "emit_coverage_diagnostics", False)` to avoid `AttributeError`.

## User Setup Required

None — no external services or environment configuration required.

## Next Phase Readiness

- Phase 71 Wave 2 can now generate diagnostics for W2a and a control anchor and write a Phase 72 handoff recommendation using the emitted summary artifacts.

---
*Phase: 71-coverage-diagnostics-failure-analysis*
*Completed: 2026-04-18*

