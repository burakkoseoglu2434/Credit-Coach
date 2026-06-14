# Plan 61-01 Summary

Implemented the canonical Phase 61 recoverability signal helper in `credit-coach/src/credit_coach/evaluation/recoverability.py`.

What shipped:
- Raw `approval_gap = max(0, base_pd - tau)`
- `normalized_gap`, `risk_band`, `recoverability_bucket`, and gap-only `recoverability_score`
- Deterministic `threshold_reach_possible`
- Additive path flags and hard-vs-soft structural blocker separation
- Compositional `recoverable_reason_codes`
- Public exports via `credit-coach/src/credit_coach/evaluation/__init__.py`

Verification:
- `cd credit-coach && python -m pytest tests/test_recoverability_signals.py -q`
- Result: `7 passed`

Notes:
- Phase 61 remains signal-only.
- No recoverable classification, recourse gating, or planner behavior changes were introduced here.
