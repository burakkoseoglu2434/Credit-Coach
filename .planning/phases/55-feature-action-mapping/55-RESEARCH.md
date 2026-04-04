# Phase 55: Feature -> Action Mapping - Research

## Objective

Research how to implement Phase 55: Feature -> Action Mapping.
Answer: "What do we need to know to plan deterministic feature -> action mapping well without reopening trust or planner behavior?"

## Codebase Findings

### 1. The canonical mapping seam already exists, but it is only partially populated

The core seam is `credit-coach/src/credit_coach/recourse/action_space.py`.

Today it already provides:
- `ACTION_CATALOG` for the canonical Phase 54 action taxonomy
- `ACTION_SPACE` for feature-level `ActionSpec`
- `get_action_spec()`, `get_action_metadata()`, and `get_numeric_target_metadata()`
- coverage validation against `credit-coach/configs/features_48.yaml`

Current state:
- 47 modeled features exist in `features_48.yaml`
- 21 features are currently marked `actionable=True`
- 26 features are currently marked `actionable=False`

This means current runtime actionable coverage is `21 / 47 = 44.7%`, well below `MAP-03`'s `>= 80%` feature-to-action coverage target.

### 2. Phase 55 should separate "mapping coverage" from "runtime actionable"

The most important brownfield constraint is that the system already uses `actionable=True` as a runtime behavior flag.

If Phase 55 simply flips many more features to `actionable=True`, it risks reopening:
- planner candidate behavior
- DICE contender behavior
- trust and winner-integrity assumptions

The safer approach is:
- keep runtime `actionable` semantics stable for now
- add a separate deterministic mapping layer for all 47 modeled features
- classify each feature as:
  - primary actionable mapping
  - supporting actionable mapping
  - non-actionable

This satisfies the mapping goal without changing current selection or execution semantics.

### 3. Existing canonical action groups are already strong enough for grouped mapping

`ACTION_CATALOG` already exposes the grouped action families needed for Phase 55:
- `refinance`
- `debt_consolidation`
- `improve_payment_consistency`
- `credit_limit_adjustment`
- `installment_plan`

These groups already include:
- `primary_features_impacted`
- `primary_target_feature_name`
- `action_owner`
- `action_category`
- `action_type`
- `dice_eligible`
- `heuristic_only`
- `requires_numeric_target`
- `requires_institutional_approval`

Phase 55 can therefore expand feature coverage mostly by:
- assigning more features to an existing canonical action
- designating whether each mapped feature is `primary` or `supporting`
- adding explicit non-actionable reasons where no safe single interpretation exists

### 4. `features_48.yaml` is the denominator and must stay authoritative

`credit-coach/configs/features_48.yaml` is the canonical inventory.

That file contains:
- 47 modeled features
- 1 target label (`target`)

Phase 55 must map the 47 modeled features only.
The target label is not a feature-to-action input and should remain out of scope.

### 5. There is a brownfield compatibility gap in downstream consumers

The current codebase still contains legacy semantic fields outside `action_space.py`:
- `credit-coach/src/credit_coach/data/schema.py`
  - `ActionBusinessView` still exposes `action_family` / `action_class`
  - `PlanAction.populate_action_views()` still tries to read `template.action_class` and `template.action_family`, which Phase 54 removed from `ActionTemplate`
- `credit-coach/src/credit_coach/recourse/generator.py`
  - still requests `action_class` / `action_family` from `get_action_metadata()`
- `credit-coach/src/credit_coach/coaching/planner.py`
  - still considers `action_family` / `action_class` in its visibility checks

This means Phase 55 should avoid schema-wide redesign, but planning should explicitly account for additive compatibility checks. Mapping work cannot assume the rest of the stack is fully migrated to Phase 54 semantics yet.

### 6. The safest implementation center is still `action_space.py`

The cleanest implementation posture is:
- keep the source of truth in `action_space.py`
- add explicit mapping metadata there
- extend tests there first
- prove downstream compatibility through tests before changing any broader consumer contract

This keeps Phase 55 tightly scoped around deterministic mapping rather than dispersing logic across planner, messaging, or decision layers.

## Recommended Planning Implications

### A. Add a feature-mapping contract that is richer than `actionable`

Phase 55 likely needs new per-feature mapping metadata such as:
- `mapping_status`
- `mapping_role`
- `non_actionable_reason`

Those fields should be validated for all 47 modeled features.

### B. Do not widen runtime candidate behavior in this phase

Phase 55 should not use mapping coverage as a proxy for runtime candidate expansion.

Specifically:
- a feature can be mapped without becoming runtime-actionable
- supporting features can inherit action semantics without becoming primary optimization levers
- DICE/runtime expansion belongs to later phases

### C. Coverage target should be proven by inventory, not by hand-waving

To satisfy `MAP-03`, Phase 55 should add:
- a deterministic inventory/export helper
- coverage summary helpers
- tests proving the mapped/non-mapped denominator exactly matches `features_48.yaml`

### D. Non-actionable classification must be explicit and reasoned

A non-actionable feature should never be left as "just false."
It should carry a reason such as:
- historical fact
- identity/geography
- descriptive context only
- policy/metadata only
- no safe single action interpretation

## Impacted Files

Primary:
- `credit-coach/src/credit_coach/recourse/action_space.py`
- `credit-coach/tests/test_action_space.py`

Likely secondary for compatibility proof:
- `credit-coach/src/credit_coach/data/schema.py`
- `credit-coach/src/credit_coach/recourse/generator.py`
- `credit-coach/tests/test_recourse_redesign.py`
- `credit-coach/tests/test_messaging.py`

## Validation Architecture

Validation should prove both correctness and non-regression:

1. Mapping correctness
- all 47 modeled features classified
- no mapped feature resolves to more than one canonical action
- grouped actions have exactly one primary target feature
- every non-actionable feature has an explicit reason

2. Coverage proof
- mapped feature count is explicit and testable
- `MAP-03` coverage is computed from the canonical denominator in `features_48.yaml`

3. Brownfield safety
- existing runtime actionable helpers still behave as intended
- current actionable feature metadata still exposes stable numeric-target behavior
- existing business-view and messaging tests remain green unless explicitly updated in additive ways

Recommended test commands:
- Quick: `cd credit-coach && python -m pytest tests/test_action_space.py -q`
- Broader regression: `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_recourse_redesign.py tests/test_messaging.py tests/test_dice_lane_validity_enforcement.py -q`

## RESEARCH COMPLETE
