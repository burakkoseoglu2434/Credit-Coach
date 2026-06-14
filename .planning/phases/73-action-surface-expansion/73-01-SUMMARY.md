---
phase: 73-action-surface-expansion
plan: 01
status: complete
updated: 2026-06-14T14:11:29Z
---

## What was built
Added top-k=2 action selection for full-tier customers in `run_recourse.py` and projected new `selected_secondary_*` fields while leaving action #1 (the winner) completely untouched. Proved the behavior with 6 new unit tests plus 1 drift-guard test.

## Implementation Details
- `_select_secondary_action_for_full_mode`: Sorts by rank, filters out `institution` actions, requires a distinct action family from action #1, returns first match.
- `_action_family_for_key` and `_is_institutional_action`: Added to support selection criteria using `ACTION_CATALOG` and `LEGACY_ACTION_FAMILY_BY_ACTION_KEY`.
- `selected_secondary_*` projection: Additive fields projected during `_build_selected_surface_projection` in full-mode.
- `selected_action_count` bump: Bumps from 1 to 2 when a secondary action is surfaced. A repo-wide grep confirmed no unguarded `< 2` or `== 1` assumptions exist that a full-tier value of 2 would break. The drift guard in `run_customer_artifact_collection.py:381` is verified to not trip (tested via `test_full_mode_action_count_two_does_not_trip_drift_guard`).
- Action #1, assisted_full, and limited paths are byte-unchanged.

## Self-Check: PASS
