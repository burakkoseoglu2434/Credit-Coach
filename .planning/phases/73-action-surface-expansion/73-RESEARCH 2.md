# Phase 73: Action Surface Expansion - Research

**Researched:** 2026-06-14
**Domain:** Python recourse/recommendation surfacing pipeline (credit-coach), additive top-k action surfacing + cohort metrics
**Confidence:** HIGH

## Summary

Phase 73 is a small, well-bounded additive change to an existing, mature pipeline. The codebase already carries everything needed for top-k=2 surfacing: every candidate plan's steps carry `action_key` / `action_family` / `action_class` (from `action_space.py`'s `LEGACY_ACTION_FAMILY_BY_ACTION_KEY`), and `run_recourse.py` already builds a per-customer, rank-ordered list of grouped "paths" (`out["paths"]`, a list of `RecoursePathRecord`-shaped dicts with `path_rank`, `action_keys`, `action_owners`, `action_categories`, `rankable_flag`, `selected_path_flag`, `customer_summary`/`operator_summary`) via `_attach_path_summary_to_roadmap`, which runs **before** `_apply_recourse_gate_to_roadmap` in the main pipeline (`run_recourse.py` lines ~3815-3831).

Critically, empirical inspection of the n=500 W2a control run shows that **today's selected ("winner") plans for `full`-tier customers are single-step** (`action_count=1`), and other ranked-but-not-selected paths in the same customer's pool frequently carry a **different action_key mapping to a different `action_family`** (e.g., winner = `adjust_requested_loan_amount` / family `application_sizing`; rank-2 alternative = `debt_consolidation` / family `debt_restructuring`, path_type=`hybrid`). This means **action #2 for top-k=2 should be sourced from `roadmap["paths"]` (the customer's other rankable, non-selected paths), filtered by `rankable_flag=true`, ordered by `path_rank`, and the first one whose `action_keys[0]` maps to an `action_family` distinct from action #1's family** — not from "the selected plan's own action set" (which in observed data has only 1 action). This interpretation satisfies D-02's intent (diversity-first, keep winner unchanged, fill #2 from next-best distinct family) using data structures that already exist and are already computed pre-gate.

No new packages are required — this is a pure Python logic change within the existing `credit_coach` package plus additive CSV/JSON columns in cohort evaluation artifacts.

**Primary recommendation:** Implement top-k=2 selection inside `_apply_recourse_gate_to_roadmap` (gated on `recourse_mode == "full"`), sourcing action #2 from `out["paths"]` (already attached pre-gate), selecting the highest-ranked `rankable_flag=true`, non-selected path whose primary `action_family` differs from action #1's, excluding `action_type == "institutional"` (i.e. `action_owner == "institution"`) candidates for action #2. Project action #2 as new additive `selected_secondary_*` fields alongside the existing `selected_recommendation_*` fields (action #1 untouched). Publish action-type/family distribution metrics as a new `action_type_distribution_table` in the Phase 60 evidence bundle (`cohort_evidence.py`), following the existing `selected_path_distribution_table` pattern.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Action #2 candidate selection (diversity-first, distinct family) | API / Backend (recourse gate logic, `recoverability.py` + `run_recourse.py`) | — | Selection/ranking logic is a backend/business-logic concern; must reuse pre-gate `out["paths"]` computed in the same process |
| Action #2 narrative/projection (localized text) | API / Backend (`run_recourse.py` projection layer) | — | Same seam that already projects action #1's `selected_recommendation_text*`; must reuse existing localized payload helpers |
| `recourse_mode == "full"` gating of top-k | API / Backend (`evaluation/recoverability.py` + `run_recourse.py` gate) | — | `build_recourse_gate` is the single source of truth for tier; top-k branch must read this output, not re-derive it |
| Action-type/family distribution metrics | API / Backend / Evaluation (`run_v24_cohort_evaluation.py` + `evaluation/cohort_evidence.py`) | Database / Storage (CSV/JSON artifacts) | Cohort evaluation aggregates per-customer rows into population-level distribution tables; output is file-based artifacts, not a live service |
| Trust-counter preservation (`selected_invalid_winner_count`, `selected_surface_drift_count`, `operator_packet_contradiction_count`) | API / Backend (`run_v24_cohort_evaluation.py` flag computations) | — | These are computed from `roadmap_summary`/`metrics_summary`; additive fields must not alter the inputs these flags read |

## Standard Stack

This phase introduces **no new external dependencies**. All work is within the existing `credit_coach` Python package (pandas, pydantic already in use).

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pandas | (existing, pinned in repo) | CSV/JSON cohort artifact construction | Already used throughout `run_v24_cohort_evaluation.py` and `cohort_evidence.py` |
| pydantic | (existing, `RecoursePathRecord` in `data/schema.py`) | Path record schema (`action_keys`, `path_rank`, `rankable_flag`, etc.) | Already the schema backbone for `paths` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| (none new) | — | — | — |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Sourcing action #2 from `roadmap["paths"]` (cross-plan, pre-gate) | Sourcing action #2 from within the selected plan's own `phases[*].steps` | Selected plans in observed data are single-step (`action_count=1`); this source would almost never yield a second distinct-family action, defeating SURF-01's intent |

**Installation:** N/A — no new packages.

**Version verification:** N/A — no new packages to verify against a registry.

## Package Legitimacy Audit

**Not applicable.** Phase 73 installs no new external packages. No `package-legitimacy check` run required.

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
Per-customer recourse pipeline (run_recourse.py main flow, ~line 3800-3880)
====================================================================

[candidate_pool: list[PlanRecord]]
        |
        v
[group into RecoursePathRecord paths]  --(pathing.py)-->  path_records: list[RecoursePathRecord]
        |                                                  - path_rank (1=best, 2=next, ...)
        |                                                  - action_keys[0] -> action_family via action_space.py
        |                                                  - rankable_flag, selected_path_flag
        |                                                  - customer_summary / operator_summary (localized)
        v
[_build_customer_roadmap]  -->  roadmap (best plan -> phases/steps/narrative, summary.best_plan_id)
        |
        v
[_attach_path_summary_to_roadmap(roadmap, path_records)]
        |   roadmap["paths"] = [record.model_dump() for record in path_records]   <-- ALREADY AVAILABLE PRE-GATE
        v
[_inject_decision_inputs_into_roadmap]
        |
        v
[_apply_decision_ownership_to_roadmap]
        |
        v
[_attach_recoverability_signal_to_roadmap]
        |
        v
[_apply_recourse_gate_to_roadmap(roadmap)]   <-- NEW TOP-K=2 LOGIC GOES HERE
        |   - build_recourse_gate(summary) -> recourse_mode in {full, assisted_full, limited}
        |   - IF recourse_mode == "full":
        |       action1_family = family(selected winner's primary action_key)
        |       FOR path in roadmap["paths"] sorted by path_rank:
        |         IF path.rankable_flag AND NOT path.selected_path_flag
        |            AND family(path.action_keys[0]) != action1_family
        |            AND action_owner(path.action_keys[0]) != "institution":
        |           action2 = path  (break)
        |       attach selected_secondary_* fields to summary (additive)
        |   - existing assisted_full / limited branches UNCHANGED
        v
[_build_selected_surface_projection(roadmap)]
        |   - projects selected_recommendation_text* (action #1, UNCHANGED)
        |   - NEW: projects selected_secondary_recommendation_text* (action #2, if present)
        v
[customer_roadmap.json output]  -->  consumed by run_v24_cohort_evaluation.py
        |
        v
[run_v24_cohort_evaluation.py: per-customer row construction]
        |   - reads roadmap_summary.selected_secondary_* fields (additive columns in customer_level_analysis.csv)
        v
[_aggregate_metrics / cohort_evidence.py]
        |   - NEW: action_type_distribution_table (population-level action_family / action_type shares)
        v
[phase_60/ evidence artifacts: phase_60_cohort_eval_action_type_distribution_table.csv + .json/.md summary]
```

### Recommended Project Structure

No new files/directories. Modify in place:

```
credit-coach/src/credit_coach/
├── evaluation/
│   ├── recoverability.py        # (read-only reference) recourse_mode gating — DO NOT MODIFY gate logic
│   └── cohort_evidence.py        # ADD: action_type_distribution_table builder + writer
├── cli/
│   ├── run_recourse.py           # ADD: top-k=2 selection inside _apply_recourse_gate_to_roadmap (full-mode branch)
│   │                              # ADD: selected_secondary_* projection inside _build_selected_surface_projection
│   └── run_v24_cohort_evaluation.py  # ADD: read selected_secondary_* into customer_row; feed action_type_distribution
└── recourse/
    ├── action_space.py            # READ-ONLY: action_family() / LEGACY_ACTION_FAMILY_BY_ACTION_KEY (source of truth for "distinct family")
    └── generator.py                # READ-ONLY: action_family already attached to PlanAction via action_metadata
```

### Pattern 1: Diversity-First Action #2 Selection from `roadmap["paths"]`

**What:** Inside `_apply_recourse_gate_to_roadmap`, after `gate = build_recourse_gate(summary)` and only when `recourse_mode == "full"`, scan `out.get("paths", [])` (already attached by `_attach_path_summary_to_roadmap`, which runs earlier in the pipeline — verified at `run_recourse.py` lines 3815/3831) for the first `rankable_flag=true`, non-`selected_path_flag` path whose primary action family differs from action #1's.

**When to use:** Only for `recourse_mode == "full"`. Do not run for `assisted_full` (Phase 72 locked contract: exactly 1 action) or `limited` (0 actions).

**Example:**
```python
# Source: derived from credit_coach/src/credit_coach/cli/run_recourse.py
# (existing _apply_recourse_gate_to_roadmap, _attach_path_summary_to_roadmap,
#  and credit_coach/src/credit_coach/recourse/action_space.py LEGACY_ACTION_FAMILY_BY_ACTION_KEY)

from credit_coach.recourse.action_space import LEGACY_ACTION_FAMILY_BY_ACTION_KEY, ACTION_CATALOG

def _action_family_for_key(action_key: str) -> str | None:
    return LEGACY_ACTION_FAMILY_BY_ACTION_KEY.get(str(action_key or "").strip())

def _is_institutional_action(action_key: str) -> bool:
    template = ACTION_CATALOG.get(str(action_key or "").strip())
    return bool(template and template.action_owner == "institution")

def _select_secondary_action_for_full_mode(
    roadmap: dict,
    *,
    primary_action_key: str,
) -> dict | None:
    primary_family = _action_family_for_key(primary_action_key)
    paths = roadmap.get("paths", [])
    if not isinstance(paths, list):
        return None
    # paths is already ordered by path_rank ascending in practice, but sort defensively
    candidates = sorted(
        (p for p in paths if isinstance(p, dict)),
        key=lambda p: int(p.get("path_rank") or 999999),
    )
    for path in candidates:
        if not bool(path.get("rankable_flag", False)):
            continue
        if bool(path.get("selected_path_flag", False)):
            continue  # action #1 itself
        action_keys = path.get("action_keys") or []
        if not action_keys:
            continue
        candidate_key = str(action_keys[0])
        if _is_institutional_action(candidate_key):
            continue  # exclude action_owner == "institution" for action #2 (see Pitfall 1)
        candidate_family = _action_family_for_key(candidate_key)
        if candidate_family and candidate_family != primary_family:
            return path  # first distinct-family, rankable, non-selected path
    return None
```

### Pattern 2: Additive Projection of Action #2 (TRUST-04-safe)

**What:** Add new keys to `summary` inside `_build_selected_surface_projection` (or a new helper called from it) — never overwrite `selected_recommendation_*`, `selected_plan_id`, `best_plan_id`, or any action #1 field.

**When to use:** Only when `recourse_mode == "full"` AND a valid action #2 path was found by Pattern 1.

**Example:**
```python
# Source: pattern derived from existing _build_selected_surface_projection
# (credit_coach/src/credit_coach/cli/run_recourse.py lines ~1286-1354)

secondary_path = _select_secondary_action_for_full_mode(out, primary_action_key=primary_action_key)
if secondary_path is not None:
    secondary_payload = _localized_projection_payload(secondary_path.get("customer_summary"))
    summary.update({
        "selected_secondary_action_present": 1,
        "selected_secondary_action_key": str((secondary_path.get("action_keys") or [""])[0]),
        "selected_secondary_action_family": _action_family_for_key((secondary_path.get("action_keys") or [""])[0]),
        "selected_secondary_path_id": str(secondary_path.get("path_id") or ""),
        "selected_secondary_path_type": str(secondary_path.get("path_type") or ""),
        "selected_secondary_recommendation_text": _localized_projection_text(secondary_payload, locale="en"),
        "selected_secondary_recommendation_text_localized": secondary_payload,
    })
else:
    summary.update({
        "selected_secondary_action_present": 0,
        "selected_secondary_action_key": None,
        "selected_secondary_action_family": None,
        "selected_secondary_path_id": None,
        "selected_secondary_path_type": None,
        "selected_secondary_recommendation_text": None,
        "selected_secondary_recommendation_text_localized": None,
    })
# selected_action_count should reflect the surfaced count (1 or 2) — additive bump only for full mode
summary["selected_action_count"] = max(0, selected_action_count) + (1 if secondary_path is not None else 0)
```

**Caution:** `selected_action_count` is read downstream (`run_v24_cohort_evaluation.py` `actionable_mask`, `zero_action_flag`, `empty_state_flag`). Bumping it to 2 when action #2 is present is intentional (SURF-01 says "more than one actionable recommendation candidate"), but **double-check this does not flip any trust-counter computation** that assumes `selected_action_count <= 1` (none currently do — `actionable_mask` only checks `> 0`, `zero_action_flag` only checks `== 0`). Document this decision explicitly in the plan since it's a behavior change to a widely-read field, even though additive in spirit.

### Anti-Patterns to Avoid

- **Re-deriving `recourse_mode` inside the top-k branch:** Always read `gate["recourse_mode"]` / `summary["recourse_mode"]` from `build_recourse_gate`'s output — do not re-implement the `recoverable_flag` / `assisted_full_flag` logic. Phase 72's gate is the single source of truth.
- **Selecting action #2 from `roadmap["phases"][*]["steps"]`:** Observed selected plans for `full`-tier customers have `action_count=1` (single step). Scanning the selected plan's own steps will almost never produce a second distinct-family action. Use `roadmap["paths"]` instead (Pattern 1).
- **Mutating `selected_recommendation_text` / `selected_plan_id` / `best_plan_id`:** These are action #1's identity and must remain byte-for-byte identical (CONTEXT.md D-02, TRUST-04). All action #2 fields must be new, distinctly-named keys.
- **Padding with same-family duplicates when no distinct-family candidate exists:** CONTEXT.md D-02 explicitly forbids this — if no second distinct-family, rankable candidate exists, surface only 1 action (`selected_secondary_action_present = 0`).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Action family classification | A new family-mapping table or heuristic | `LEGACY_ACTION_FAMILY_BY_ACTION_KEY` / `ActionTemplate.action_family` in `action_space.py` | This is the canonical, validated source of truth (`validate_action_space_contract` enforces consistency); a parallel mapping would drift |
| Ranked alternative-action discovery | New ranking/scoring logic for "what's action #2" | `roadmap["paths"]` (`RecoursePathRecord`, already rank-ordered, already filters to `rankable_flag`) | Pathing/grouping (`pathing.py`) already deduplicates and ranks candidate plans into distinct paths; re-deriving this would duplicate complex logic and risk drift from the winner-selection logic |
| Localized text for action #2 | New i18n/text-generation logic | `customer_summary` / `operator_summary` already on each `RecoursePathRecord` (built via `build_recourse_path_render_payload`, same renderer used for action #1) | Reuses the exact TRUST-04-reviewed rendering pipeline; guarantees action #2's narrative style matches action #1's and stays within selected-plan evidence |

**Key insight:** Every primitive needed for top-k=2 (family classification, ranked alternatives, localized summaries) already exists and is already computed in the per-customer pipeline before the gate runs. The only "new" work is (a) a selection function that picks the right alternative, and (b) additive projection/column plumbing. Resist any temptation to add a second ranking pass, a new candidate-generation step, or a new translation/localization layer.

## Common Pitfalls

### Pitfall 1: Institutional action #2 silently changes the trust/narrative posture for `full`-tier customers
**What goes wrong:** If action #2 selection is allowed to pick a path whose `action_keys[0]` maps to `action_owner == "institution"` (i.e., `credit_limit_adjustment`, `settlement_discount`, `installment_plan` — `action_type == "institutional"` in `ACTION_CATALOG`), the surfaced output for a `full`-tier customer could now imply an institution-mediated offer as a *secondary* recommendation, which has different `requires_institutional_approval` / `offer_*` semantics than customer-only or hybrid/restructure actions.
**Why it happens:** `full`-tier customers' candidate pools can and do include institution-mediated paths (`path_type in {"institution_assisted", "hybrid"}`) ranked below the winner. `debt_consolidation` (`action_owner="hybrid"`, family `debt_restructuring`) is NOT institutional and is a good, defensible action #2 (it appeared as rank-2 for `train_026716__eval_0333` in the n=500 W2a sample). But `credit_limit_adjustment`/`settlement_discount`/`installment_plan` (`action_owner="institution"`) carry `requires_institutional_approval=True` and `offer_*` contract fields that are more complex to surface safely as an "additional" action.
**How to avoid:** Restrict action #2 candidates to paths whose primary action's `action_owner != "institution"` (equivalently, exclude `ACTION_CATALOG[action_key].action_type == "institutional"`). This allows `customer` and `hybrid` (restructure/consolidation/refinance/adjustment) families for action #2 — covering the explicit semantics named in the phase goal (refinance, consolidation, restructuring, loan-amount adjustment) — while deferring institution-assisted action #2 surfacing (consistent with Phase 72's posture of deferring institution-assisted surfacing).
**Warning signs:** A surfaced action #2 with `requires_institutional_approval=1` or non-empty `offer_type` that wasn't present in today's single-action output; `operator_packet_contradiction_count` regression in cohort eval.

### Pitfall 2: `full`-tier customers whose WINNER is already institution-assisted
**What goes wrong:** Research found **no observed cases** (across all available `customer_level_analysis.csv` runs) of a `full`-tier customer whose `selected_path_type` is `institution_assisted`/`institution`/`hybrid`, and no cases of `selected_action_count > 1` for `full`-tier in any selected plan. This means the "full-tier customers may already receive institution-assisted actions as PRIMARY winner today" scenario flagged in CONTEXT.md's discretion section is **not empirically observed in current evaluation artifacts** (n=500 W2a control + n≈96 n=3000 run + several other cohort runs checked).
**Why it happens:** The available evaluation runs are small samples (n=500, n≈96) from `near_threshold_denied`/`global_denied` cohorts; institution-assisted winners for `full` mode may exist in unobserved customer populations or simply be rare given the planner's ranking preferences (CUSTOMER_ONLY_TIEBREAK reason code observed).
**How to avoid:** Do not special-case "winner is institutional" — the selection logic in Pattern 1 works regardless of action #1's `action_owner` (it only compares `action_family`, and the action #2 exclusion in Pitfall 1 applies to action #2's owner, not action #1's). If a future run does surface an institutional winner for `full` mode, Pattern 1 still produces a correct, non-institutional action #2 (or none, if no distinct-family non-institutional alternative exists) without any additional logic.
**Warning signs:** N/A for this phase — flag as an **Open Question** for the planner/discuss-phase if a wider cohort run later reveals institutional `full`-tier winners with non-empty alternative paths.

### Pitfall 3: `selected_action_count` bump breaking downstream assumptions
**What goes wrong:** `run_v24_cohort_evaluation.py` uses `selected_action_count` for `actionable_mask` (`> 0`), `zero_action_flag` (`== 0`), and `empty_state_flag`. None of these break with values of 2, but any *new* code added in this phase that assumes `selected_action_count in {0, 1}` (e.g., a naive `if selected_action_count == 1` branch) would silently misclassify top-k=2 customers.
**Why it happens:** `selected_action_count` has been a 0/1 field since Phase 66-ish; this phase is the first to make it potentially 2.
**How to avoid:** grep for all `selected_action_count` comparisons (`run_v24_cohort_evaluation.py` lines ~853-930, `run_recourse.py` summary fields) before finalizing the plan and confirm no `== 1` / `<= 1` assumptions exist outside what was already checked here. Add a unit test asserting `selected_action_count == 2` for a `full`-tier fixture with a valid action #2.
**Warning signs:** `actionable_rate` or `empty_state_rate` shifting unexpectedly in cohort eval after this phase ships, even though no `full`-tier customer's *qualification* changed.

### Pitfall 4: `out["paths"]` not present / empty for some code paths
**What goes wrong:** `_attach_path_summary_to_roadmap` is called at two call sites in `run_recourse.py` (lines ~3400 and ~3815). If any code path reaches `_apply_recourse_gate_to_roadmap` WITHOUT `out["paths"]` populated (e.g., a future refactor, or a different CLI entry point that builds a roadmap dict manually for tests), `out.get("paths", [])` will be empty and action #2 selection silently returns `None` — degrading gracefully to today's 1-action output. This is SAFE (no crash, no trust violation) but should be tested explicitly so it's not mistaken for a bug.
**Why it happens:** `_apply_recourse_gate_to_roadmap` is also called in test fixtures (`test_recourse_gate_relaxation.py`'s `_roadmap()` helper) that construct minimal roadmap dicts WITHOUT a `paths` key.
**How to avoid:** Use `out.get("paths", [])` (not `out["paths"]`) defensively; add a test asserting that a roadmap dict with no `paths` key in `full` mode surfaces exactly 1 action (`selected_secondary_action_present == 0`) without raising.
**Warning signs:** `KeyError: 'paths'` in any test or a `full`-mode roadmap unexpectedly missing `selected_secondary_*` keys (should always be present, even if `None`/`0`, per Pattern 2).

## Code Examples

### Reading action family for a candidate path's primary action

```python
# Source: credit_coach/src/credit_coach/recourse/action_space.py (existing, read-only)
from credit_coach.recourse.action_space import LEGACY_ACTION_FAMILY_BY_ACTION_KEY

LEGACY_ACTION_FAMILY_BY_ACTION_KEY = {
    "adjust_requested_loan_amount": "application_sizing",
    "refinance": "debt_restructuring",
    "increase_regular_income": "income_growth",
    "verify_income_documentation": "cashflow_management",
    "reduce_spending": "cashflow_management",
    "debt_consolidation": "debt_restructuring",
    "limit_credit_usage": "utilization",
    "improve_payment_consistency": "payment_behavior",
    "credit_limit_adjustment": "limit_management",     # action_owner="institution"
    "settlement_discount": "hardship_relief",          # action_owner="institution"
    "installment_plan": "hardship_relief",             # action_owner="institution"
}
```

Note: `refinance` and `debt_consolidation` are BOTH `debt_restructuring` family but different `action_key`s and different `action_owner`s (`refinance`=hybrid, `debt_consolidation`=hybrid). If action #1 is `refinance`, a candidate `debt_consolidation` path would NOT count as a distinct family for action #2 (same family) — per CONTEXT.md's "Specific Ideas" section, distinctness is by **family**, not by action key.

### Existing per-customer `paths` shape (from `RecoursePathRecord`, already attached pre-gate)

```python
# Source: observed in credit-coach/artifacts/evaluations/v27_w2a_control_eval_20260420_full_processed_n500_seed42/path_groupings.jsonl
# (this is the cohort-eval mirror of roadmap["paths"]; same RecoursePathRecord shape)
{
    "path_id": "train_026716__eval_0333_path_a00f467f83dd",
    "path_type": "hybrid",
    "rankable_flag": true,
    "path_rank": 2,
    "representative_plan_id": "v24_cohort_eval_42_train_026716__eval_0333_rule_1",
    "action_keys": ["debt_consolidation"],
    "action_owners": ["hybrid"],
    "action_categories": ["credit_structure"],
    "selected_path_flag": false,
    "customer_summary": {
        "tr": "donen borc bakiyesi seviyesini 8,416 birim'den 6,564.5 birim seviyesine indir. Teklif aktif durumda.",
        "en": "Reduce revolving balance from 8,416 units to 6,564.5 units. Offer is currently active."
    }
}
```

For this same customer, `path_rank=1` (`selected_path_flag=true`) is `action_keys=["adjust_requested_loan_amount"]` (family `application_sizing`). The `path_rank=2` path above has `action_keys=["debt_consolidation"]` (family `debt_restructuring`, owner `hybrid`, NOT institutional) — a valid action #2 candidate under Pattern 1.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| 1 surfaced action for `full`-tier (`selected_action_count` always 0 or 1) | Up to 2 surfaced actions for `full`-tier when a distinct-family rankable alternative exists | Phase 73 (this phase) | `selected_action_count` can now be 2; new `selected_secondary_*` fields appear in roadmap summary and cohort CSVs |
| `selected_path_distribution_table` (customer-only/institution-assisted/hybrid winner shares only) | + new `action_type_distribution_table` (action_family / action_type shares across BOTH surfaced actions for `full`-tier) | Phase 73 (this phase) | Enables SURF-03 dominance detection (no single action family > 50% per milestone acceptance bar) |

**Deprecated/outdated:** None — this phase adds to the existing v2.5-v2.7 contract surface; nothing is removed.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `roadmap["paths"]` is populated (non-empty) for the majority of `full`-tier customers with ≥2 rankable paths of distinct families, making top-k=2 surfacing materially non-trivial (not a rare edge case) | Summary / Pattern 1 | If most `full`-tier customers only have 1 rankable path total, SURF-03's "reduced single-action dominance" success criterion may not move much; the plan should include an evaluation step to quantify how often action #2 is actually found, and treat near-zero uplift as a valid (if underwhelming) outcome rather than a bug |
| A2 | "Distinct action family" should be computed from `action_keys[0]` (the path's PRIMARY/representative action), not from a union of all action_keys across a path's member plans | Pattern 1, Code Examples | If a path's `action_keys` list has multiple entries with different families, restricting to `[0]` could miss a valid distinct-family match that exists deeper in the same path; however, `path_signature`/`action_keys` in observed data are single-element lists for both rank-1 and rank-2 paths, so this is low-risk in practice |
| A3 | Excluding `action_owner == "institution"` (action_type == "institutional") candidates for action #2 is the "least-disruptive, most-defensible rule" requested by CONTEXT.md's discretion item #1 | Pitfall 1 | If product/stakeholders want institution-mediated actions (e.g., `credit_limit_adjustment`) surfaced as action #2 for `full`-tier customers, this assumption under-delivers on SURF-02's "existing internal action semantics" framing; however it is consistent with Phase 72's precedent of deferring institutional surfacing, and is the safer default for a TRUST-04-bounded additive phase |
| A4 | Bumping `selected_action_count` to 2 (rather than leaving it at 1 and introducing a separate `surfaced_action_count`) is safe for all downstream trust-counter computations | Pattern 2, Pitfall 3 | If any hidden downstream consumer (outside `run_v24_cohort_evaluation.py` and `run_recourse.py`, e.g. a dashboard or report not grepped in this research) assumes `selected_action_count <= 1`, bumping it could silently change that consumer's output; the plan should include a repo-wide grep for `selected_action_count` as a Wave 0 verification step |

## Open Questions

1. **Does a wider cohort (n=3000+) reveal `full`-tier customers with institution-assisted or hybrid PRIMARY winners, or with selected plans where `action_count > 1`?**
   - What we know: In all currently-available evaluation artifacts (n=500 W2a control, n≈96 "n3000" run, several Phase 71/72 runs), every `full`-tier customer's selected plan has `action_count=1` and `selected_path_type=customer_only`.
   - What's unclear: Whether this holds at the full n=3000 (or larger) scale referenced in STATE.md's "Open Carry-Forward Items" (the recommended-but-not-yet-run re-run).
   - Recommendation: The plan should not assume single-step `full`-tier winners are universal, but Pattern 1's logic is robust to either case (it only needs `roadmap["paths"]` to contain ≥1 other rankable, distinct-family, non-institutional path). Treat this as a verification step in the Phase 73 evaluation, not a blocker to implementation.

2. **Should `action_type_distribution_table` report distribution over surfaced actions (action #1 + action #2 combined) or separately for action #1 vs action #2?**
   - What we know: SURF-03 requires "action-type distribution metrics... so dominance by a single action family can be detected." The existing `selected_path_distribution_table` reports shares for the WINNER (action #1) only.
   - What's unclear: Whether cohort consumers need action #1 and action #2 distributions separately (to see if action #2 specifically reduces dominance) or combined (overall surfaced-action family mix).
   - Recommendation: Publish BOTH — a combined `action_type_distribution_table` (over all surfaced action slots, weighting each surfaced action equally) for the headline SURF-03 metric, AND retain per-slot breakdowns (`action1_family_distribution`, `action2_family_distribution` as dict-valued columns, following the existing `recourse_mode_distribution`-style dict-in-cell pattern used in `phase_60_cohort_eval_recourse_gate_table.csv`). This is additive and lets the planner choose the headline metric without re-deriving from raw data later.

## Environment Availability

No external dependencies. This phase modifies existing Python modules within `credit-coach/src/credit_coach/` and existing test/evaluation CLIs. Python 3.13, pandas, and pydantic are already present in the repo's environment (confirmed by existing `.pyc` cache files for pytest 8.3.4 under `credit-coach/tests/__pycache__/`).

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | All modules | Yes (per existing `.pyc` artifacts) | 3.13 | — |
| pytest 8.3.4 | Test suite | Yes (per existing `.pyc` artifacts) | 8.3.4 | — |
| pandas | Cohort artifact CSV/JSON writers | Yes (already imported throughout `run_v24_cohort_evaluation.py`, `cohort_evidence.py`) | (repo-pinned) | — |

**Missing dependencies with no fallback:** none
**Missing dependencies with fallback:** none

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 |
| Config file | none found at repo root for credit-coach (relies on `PYTHONPATH=src` convention seen in Phase 72 verification: `cd credit-coach && PYTHONPATH=src python3 -m pytest ...`) |
| Quick run command | `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_recourse_gate_relaxation.py -q` |
| Full suite command | `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/ -q -k "recourse or recoverab or cohort"` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SURF-01 | `full`-tier customer with ≥2 distinct-family rankable paths surfaces 2 actions (`selected_action_count == 2`, `selected_secondary_action_present == 1`) | unit | `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_recourse_gate_relaxation.py -k top_k -x` | ❌ Wave 0 (new test function needed) |
| SURF-01 | `full`-tier customer with only 1 rankable path (or no distinct-family alternative) surfaces exactly 1 action, unchanged (`selected_action_count == 1`, `selected_secondary_action_present == 0`) | unit | same file, new test | ❌ Wave 0 |
| SURF-02 | Action #2 (when present) uses an existing supported `action_family` (`adjust_requested_loan_amount`/`refinance`/`debt_consolidation`/etc.), never a synthesized/new semantic | unit | assert `selected_secondary_action_key in LEGACY_ACTION_FAMILY_BY_ACTION_KEY` | ❌ Wave 0 |
| SURF-02 | Action #2 excludes `action_owner == "institution"` candidates | unit | new test with a `paths` fixture where rank-2 is `credit_limit_adjustment` (institutional) and rank-3 is `debt_consolidation` (hybrid) — assert action #2 == rank-3 | ❌ Wave 0 |
| SURF-03 | Cohort evaluation emits `action_type_distribution_table` with non-empty family/type distributions for `full`-tier population | integration | `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_recourse_funnel_kpis.py -k action_type_distribution -x` (or new test module) | ❌ Wave 0 |
| TRUST-04 | `assisted_full` and `limited` tiers remain unaffected (existing 6/6 tests in `test_recourse_gate_relaxation.py` still pass) | regression | `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_recourse_gate_relaxation.py -q` | ✅ exists (6 tests, currently passing) |
| TRUST-04 | Action #2's narrative text comes from `customer_summary`/`operator_summary` (existing rendering pipeline), never invents claims beyond the alternative path's own data | unit | assert `selected_secondary_recommendation_text == <path's customer_summary.en>` | ❌ Wave 0 |
| TRUST-01/02/03 | Trust counters (`selected_invalid_winner_count`, `selected_surface_drift_count`, `operator_packet_contradiction_count`) remain 0 after top-k=2 change | integration | re-run Phase 72's evidence pipeline on the same n=500 fixture and diff trust counters | ✅ existing pipeline (`run_v24_cohort_evaluation.py`), needs re-run as part of Phase 73 evaluation |

### Sampling Rate
- **Per task commit:** `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_recourse_gate_relaxation.py -q`
- **Per wave merge:** `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/ -q -k "recourse or recoverab or cohort or rendering"`
- **Phase gate:** Full suite green before `/gsd-verify-work`, plus an n=500 (minimum) cohort re-run comparing pre/post Phase 73 trust counters and `action_type_distribution_table`.

### Wave 0 Gaps
- [ ] New unit tests in `credit-coach/tests/test_recourse_gate_relaxation.py` (or a new `test_recourse_action_surface_expansion.py`) covering SURF-01/SURF-02/TRUST-04 top-k=2 selection scenarios, following the existing `_roadmap()` fixture builder pattern (will need a `"paths": [...]` key added to that fixture).
- [ ] New test(s) for `action_type_distribution_table` construction in `cohort_evidence.py` / `run_v24_cohort_evaluation.py`, following the existing `selected_path_distribution_table` test pattern (locate via `grep -rn "selected_path_distribution" credit-coach/tests/`).
- [ ] Repo-wide grep for `selected_action_count` usages outside `run_recourse.py` and `run_v24_cohort_evaluation.py` to confirm no hidden `<= 1` assumptions (Assumption A4 / Pitfall 3).
- [ ] Framework install: none needed — pytest already present.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Phase is internal pipeline/CLI logic; no auth surface touched |
| V3 Session Management | No | N/A |
| V4 Access Control | No | N/A — no new API endpoints or access boundaries |
| V5 Input Validation | Marginal | `roadmap["paths"]` entries are produced internally by `pathing.py` from already-validated `PlanRecord`/`RecoursePathRecord` pydantic models; new code should use `.get()` with defaults (as in Pattern 1) rather than assuming keys exist, to avoid `KeyError`/`TypeError` on malformed dicts in test fixtures or future schema drift |
| V6 Cryptography | No | N/A |

### Known Threat Patterns for {stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Narrative/claim drift — surfacing action #2 with text/claims not backed by the underlying path's own evidence (violates TRUST-04, which is itself a STRIDE "Repudiation"/"Information Disclosure"-adjacent integrity concern for a credit-recommendation product) | Tampering (of evidence-to-narrative mapping) | Reuse `customer_summary`/`operator_summary` and `_localized_projection_payload`/`_localized_projection_text` exactly as action #1 does; never construct new narrative strings from raw feature deltas for action #2 |
| Trust-counter silent regression — additive fields inadvertently change `selected_action_count`-derived flags, masking a real validity/drift issue under "expected" 2-action noise | Repudiation | Re-run the full trust-counter computation (`selected_invalid_winner_flag`, `selected_surface_drift_flag`, `operator_packet_contradiction_flag`) on a Phase-73-modified n=500 cohort and diff against the Phase 72 baseline (`72-REPORT.md` numbers: all three counters = 0) before declaring the phase done |

## Sources

### Primary (HIGH confidence)
- `credit-coach/src/credit_coach/recourse/action_space.py` (read in full) — `LEGACY_ACTION_FAMILY_BY_ACTION_KEY`, `ACTION_CATALOG`, `ActionTemplate.action_family`/`action_class`/`action_owner`
- `credit-coach/src/credit_coach/cli/run_recourse.py` — `_apply_recourse_gate_to_roadmap` (lines 908-1037), `_build_selected_surface_projection` (lines 1286-1354), `_attach_path_summary_to_roadmap` (lines 410-439), call-order verification (lines 3815/3831)
- `credit-coach/src/credit_coach/evaluation/recoverability.py` — `build_recourse_gate` (lines 171-184), `build_narrative_posture` (lines 187+)
- `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py` — `_aggregate_metrics` (lines 779-940+), customer row construction (lines 1638-1845)
- `credit-coach/src/credit_coach/evaluation/cohort_evidence.py` — `build_phase60_evidence_summary`, `write_phase60_evidence_artifacts` (lines 441-640), `selected_path_distribution_table` pattern
- `credit-coach/src/credit_coach/data/schema.py` — `RecoursePathRecord` (lines 1595+)
- `credit-coach/tests/test_recourse_gate_relaxation.py` — existing fixture pattern (`_roadmap()` helper, 6 passing tests)
- Live evaluation artifacts: `artifacts/evaluations/v27_w2a_control_eval_20260420_full_processed_n500_seed42/{customer_level_analysis.csv, candidate_plans.jsonl, path_groupings.jsonl, selected_plans.jsonl}` — confirmed empirically that `full`-tier winners are single-step and that rank-2 alternatives can carry distinct `action_family`

### Secondary (MEDIUM confidence)
- `.planning/phases/72-recoverability-gate-relaxation-controlled/72-VERIFICATION.md` — confirms Phase 72 shipped trust-clean (6/6), recommends "Go" for Phase 73, and flags n=500 vs n=3000 evidence gap

### Tertiary (LOW confidence)
- None — all findings above were verified directly against code and live artifacts in this repo.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; entirely existing-codebase reuse, verified by reading source
- Architecture: HIGH — selection seam (`_apply_recourse_gate_to_roadmap` + pre-attached `roadmap["paths"]`) verified by reading call order and live artifact shapes
- Pitfalls: HIGH — institutional-action exclusion and `selected_action_count` semantics verified against `ACTION_CATALOG` and `run_v24_cohort_evaluation.py` usage sites; "no observed institutional full-tier winners" verified empirically across all available cohort runs (with explicit caveat about sample size in Open Questions)

**Research date:** 2026-06-14
**Valid until:** 2026-07-14 (30 days — stable internal codebase, no fast-moving external dependencies)
