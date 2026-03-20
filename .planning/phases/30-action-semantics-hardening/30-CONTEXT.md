# Phase 30: Action Semantics Hardening - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Turn feature deltas into a deterministic, typed, and product-safe action semantics layer so the system no longer expresses main recommendations as raw feature names. This phase locks action taxonomy, feature-to-action mapping, action grouping, serialization identity, and schema-level business vs technical view separation. It does not yet introduce numeric target generation, feasibility hardening, execution modeling, richer offer logic, expanded narratives, product-surface upgrades, portfolio proof refresh, calibration, or pilot integration.

</domain>

<decisions>
## Implementation Decisions

### Carry-Forward Decisions From Prior Phases
- Phase 12 remains the semantic baseline:
  - the top-level action model is still hybrid
  - `action_key` is the user-facing semantic anchor
  - feature effects remain the engine-facing execution seam
- Phase 18 remains authoritative for product contract posture:
  - engine owns truth
  - website and other surfaces are typed consumers
  - business-first and technical-reveal separation should be explicit rather than UI-improvised
- Phase 19 and Phase 20 truths remain inherited:
  - execution-aware and trajectory semantics are not reopened here
  - Phase 30 is about what an action *is*, not yet whether it is likely, numerically targeted, or checkpoint-optimal

### Action Taxonomy And Mapping
- The top-level taxonomy is final and closed:
  - `behavioral`
  - `structural`
  - `institutional`
- No new top-level action class should be introduced in Phase 30.
- A second canonical layer must be added:
  - `action_family`
- `action_family` is required for product and analytics clarity, while `action_class` remains the high-level semantic bucket.
- Every actionable feature must map to exactly one primary action.
- Multi-action ambiguity at the feature level is not allowed in Phase 30.
- If one recommendation needs to express multiple effects, that must be handled through grouped or composite action semantics rather than many primary action mappings.
- Any actionable feature that cannot be mapped to a canonical primary action is a hard failure.
- Phase 30 must not tolerate unmapped actionable features through generic catch-all actions or raw-feature fallback in the default contract.

### Action Grouping And Composite Semantics
- If multiple feature effects resolve to the same primary action, the default product representation must be one grouped action rather than many separate visible steps.
- `action_group_id` must be deterministic and derived from:
  - `action_key + phase`
- Cross-class grouping is not allowed.
- A single action group must not mix:
  - `behavioral`
  - `structural`
  - `institutional`
  semantics together.
- Composite actions should appear in the default product view as:
  - one main action
- Supporting feature effects should remain visible only in the technical or effect layer.
- Phase 30 should prefer clean product semantics over exposing every low-level effect equally.

### Serialization Contract
- The default serialized identity of an action must be:
  - `action_key`
  - `action_family`
  - `action_class`
  - `action_title`
  - `action_group_id`
- `feature_name` must not remain part of the default semantic action identity.
- `feature_name` should live only in the technical or effect layer.
- Action titles and short descriptions should be fully catalog-driven and deterministic in Phase 30.
- Customer-specific narrative variation is deferred; this phase should first lock stable semantic labels.
- Phase 30 must explicitly separate:
  - `business_view`
  - `technical_view`
  at the schema level.
- This separation must not be left to UI naming convention or frontend interpretation.

### Business And Technical View Separation
- The business view should expose semantic action identity and grouped recommendation meaning without raw feature anchors.
- The technical view should preserve:
  - underlying feature effects
  - effect anchors
  - grouped sub-effects
  - any other engine-facing detail needed for traceability
- The default product-facing recommendation contract must no longer be readable as:
  - `feature_name -> target`
- Instead, product surfaces should read semantic actions by default and open the effect layer only on demand.

### Claude's Discretion
- Exact `action_family` vocabulary as long as it is stable, business-meaningful, and does not reopen top-level classes
- Exact JSON nesting for `business_view` and `technical_view` as long as the separation is explicit and machine-readable
- Exact field names for catalog-driven short description text as long as titles and descriptions remain deterministic
- Exact representation of grouped sub-effects as long as:
  - default product view stays grouped
  - technical view preserves underlying feature effects

</decisions>

<specifics>
## Specific Ideas

- The user explicitly wants the system to stop speaking in raw feature deltas such as:
  - `last_fico_range_high 614 -> 671`
- The product should instead speak in user-understandable action units.
- The user explicitly wants to lock:
  - action taxonomy
  - feature-to-action mapping
  - action grouping
  - serialization contract
  - business vs technical view separation
- The user wants Phase 30 to be intolerant of unmapped actionable features:
  - no generic fallback action
  - no raw feature recommendation in the main product contract
- Composite recommendations should appear as one action in the main surface, with low-level effect details visible only in the technical layer.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [action_space.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/action_space.py)
  - already defines:
    - `ActionClass`
    - `ActionTemplate`
    - `ActionSpec`
    - `ACTION_CATALOG`
    - `ACTION_SPACE`
  - is the canonical seam for taxonomy, mapping, and action catalog hardening
- [schema.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py)
  - already carries `PlanAction`
  - currently remains too feature-name-centric for the new Phase 30 contract
  - is the natural place to formalize `business_view` vs `technical_view` separation
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py)
  - already serializes `action_key`, `action_class`, `action_title`, `action_group_id`, and `feature_name`
  - is the main seam that currently leaks feature anchors into the top-level serialized action rows
- [messaging.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/messaging.py)
  - already uses a controlled `technical_reveal` pattern
  - is a strong precedent for Phase 30’s schema-level business vs technical separation
- [run_batch_recourse_eval.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py)
  - already emits action realism and action-class summaries
  - will be a downstream consumer once action-family and grouping semantics harden

### Established Patterns
- Phase 12 already established:
  - user-facing `action_key`
  - feature-facing effect anchor
  - `action_group_id` for composite action seams
- Phase 18 already established:
  - engine-owned output contracts
  - explicit business-first and technical-reveal product posture
- Engine artifacts remain source-of-truth; frontend or demo layers should not invent fallback semantics for unmapped actions

### Integration Points
- Primary engine seams for Phase 30:
  - `credit-coach/src/credit_coach/recourse/action_space.py`
  - `credit-coach/src/credit_coach/data/schema.py`
  - `credit-coach/src/credit_coach/cli/run_recourse.py`
- Secondary consumers that must remain compatible:
  - `credit-coach/src/credit_coach/coaching/messaging.py`
  - `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - website typed mirrors and demo consumers introduced in earlier milestones

</code_context>

<deferred>
## Deferred Ideas

- Numeric target generation belongs to Phase 31, not Phase 30
- Feasibility and constraint hardening for numeric targets belongs to Phase 32
- Action difficulty and execution modeling belongs to Phase 33
- Offer-layer restructuring belongs to Phase 34
- Personalized narrative richness belongs to Phase 35
- Demo and product-surface rollout belongs to Phase 36
- Portfolio-level personalized impact proof belongs to Phase 37
- Calibration and false-optimism validation belongs to Phase 38
- Pilot integration and real-institution loop startup belong to Phase 39

</deferred>

---
*Phase: 30-action-semantics-hardening*
*Context gathered: 2026-03-20*
