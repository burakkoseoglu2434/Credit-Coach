# Phase 46 — Dice Lane Validity Enforcement Context

**Last updated:** 2026-03-26
**Status:** Discussed and locked
**Milestone:** `v2.2 Winner Integrity & Consumer Consistency`
**Requirements:** `DICE-01`, `DICE-02`

<domain>
## Phase Boundary

Phase 46 does **not** redesign:

- Phase 40.5 deterministic decision ownership semantics
- Phase 41 cohort / calibration math or reporting structure
- Phase 42 planner-quality or source-mix semantics
- Phase 42.5 recommendation validity taxonomy or warning posture
- Phase 45 winner hard-stop chooser contract
- Phase 43 operator packet semantics
- any threshold widening or approval-rate optimization

Phase 46 **does** own:

- making the `dice` lane obey the same minimum typed-action and validity contract as internal contenders before planner selection
- converging `dice` action normalization onto the shared canonical action contract rather than keeping an ad-hoc typed-action path
- adding a lane-specific DICE quality layer for annotation completeness, semantic contender-worthiness, and contender eligibility
- distinguishing visible `dice` diagnostics from planner-eligible `dice` contenders
- adding DICE-specific artifact and rerun proof so the lane can be evaluated independently from overall winner hard-stop behavior

Guardrails:

- Phase 45 winner hard-stop remains fixed and is only consumed here
- DICE lane quality is the only north star for this phase
- diagnostics visibility must be preserved even when `dice` contenders are excluded from ranking
- consumer-surface coherence cleanup remains later `v2.2` scope

</domain>

<decisions>
## Implementation Decisions

### 1. DICE Annotation Completeness Must Converge To The Shared Owner

- DICE generation may remain a separate candidate-generation lane.
- DICE action typing and annotation may **not** remain an ad-hoc contract.
- Canonical rule:
  - feature-delta to `PlanAction` normalization should have one owner
  - internal and `dice` may differ in candidate generation
  - they may not differ in the minimum action contract used for contention
- DICE contenders must carry the same minimum typed / validity-ready contract as internal contenders:
  - `action_key`
  - `action_class`
  - `action_family`
  - `action_title`
  - `action_group_id`
  - `recommendation_validity_status`
  - `recommendation_validity_codes`
- Required when applicable:
  - `checkpoint_metric`
  - `primary_numeric_target`
  - `offer_contract`
- Missing required annotation does **not** reopen Phase 42.5 validity taxonomy.
- Instead, DICE lane carries separate quality truth:
  - `dice_annotation_complete`
  - `dice_semantic_quality_status`
  - `dice_contender_eligible`
- Annotation-incomplete DICE candidates remain visible in diagnostics but are not planner contenders.

### 2. DICE Semantic Quality Is Separate From Recommendation Validity

- Canonical distinction:
  - `recommendation_validity` answers whether the numeric recommendation is directionally / economically sane
  - `dice` semantic quality answers whether the recommendation is contender-worthy, renderable, and typed strongly enough to behave like a productized recommendation
- DICE semantic quality should evaluate at least:
  - typed annotation completeness
  - at least one surviving actionable step
  - directionally consistent action copy versus numeric target
  - business-readable recommendation renderability for metric-based actions
  - customer-vs-institution role correctness
  - step-to-text determinism for canonical rendering
- Hard semantic invalid cases:
  - zero actionable step after feasibility / constraint processing
  - missing required typed annotation
  - metric-based action without applicable `primary_numeric_target`
  - customer / institution role confusion
  - title / class / family missing badly enough that canonical recommendation text cannot be produced
- Warning cases:
  - `heuristic_fallback` backend
  - over-generic title / description fallback
  - narrow metric-family collapse without corroborating diversity
  - institution condition present but no customer-action step
- Semantic quality owner should be separate and DICE-specific:
  - `annotate_dice_candidate_quality(...)`
- Required DICE quality outputs:
  - `dice_annotation_complete`
  - `dice_semantic_quality_status = valid | warning | invalid`
  - `dice_semantic_quality_codes`
  - `dice_contender_eligible`
  - `dice_backend_class`
  - `dice_quality_gate_version`

### 3. DICE Diagnostics Pool And Planner Contender Set Must Be Separate

- Phase 46 must distinguish:
  - visible DICE candidate diagnostics
  - planner-eligible DICE contender set
- All DICE candidates may remain visible in raw / flat artifact diagnostics.
- Only DICE candidates with `dice_contender_eligible = true` may enter planner contention.
- Hard DICE contender eligibility gate:
  - `recommendation_validity_status != invalid`
  - `dice_annotation_complete = true`
  - `dice_semantic_quality_status != invalid`
  - at least one actionable step
  - contender-compatible constraint status
  - `dice_backend_class != skipped`
- Warning DICE candidates remain rankable.
- Warning ranking should carry two bounded penalty lanes:
  - existing `recommendation_warning_penalty`
  - additive `dice_semantic_warning_penalty`
- `no_valid_winner` and “no eligible DICE” are different truths.
- DICE lane should therefore carry separate counts:
  - `dice_candidate_count`
  - `dice_contender_eligible_count`
  - `dice_invalid_candidate_count`
  - `dice_warning_candidate_count`
  - `dice_all_candidates_ineligible`

### 4. DICE-Specific Diagnostics And Acceptance Proof

- Minimum plan-level additive fields:
  - `dice_backend_class`
  - `dice_annotation_complete`
  - `dice_semantic_quality_status`
  - `dice_semantic_quality_codes_json`
  - `dice_contender_eligible`
  - `dice_semantic_warning_penalty`
- Minimum metrics-level additive fields:
  - `dice_candidate_count`
  - `dice_contender_eligible_count`
  - `dice_invalid_candidate_count`
  - `dice_warning_candidate_count`
  - `dice_all_candidates_ineligible`
- `dice_backend_class` vocabulary is locked:
  - `native`
  - `heuristic_fallback`
  - `skipped`
- Required collection-level DICE aggregate lenses:
  - `dice_eligible_rate`
  - `dice_invalid_rate`
  - `dice_warning_rate`
  - `dice_fallback_rate`
  - `dice_all_ineligible_customer_rate`
  - `selected_dice_valid_rate`
- Phase 46 validation is mandatory:
  - unit coverage
  - integration coverage
  - three 250-customer reruns:
    - `pilot_mixed`
    - `risk_band_balanced`
    - `offer_needed_balanced`
- Required acceptance checks:
  - all selected `dice` winners have:
    - `dice_contender_eligible = true`
    - `dice_annotation_complete = true`
    - `dice_semantic_quality_status != invalid`
  - `0` selected `dice` winners with missing required annotation
  - `0` selected `dice` winners with semantic invalid status
  - diagnostics-pool counts and planner-eligible counts remain consistent
  - `selected_dice_valid_rate = 1.0`

### Claude's Discretion

- Exact helper and module names for the shared DICE normalization layer
- Whether DICE quality annotation lives in `run_recourse.py` or a new lane-specific recourse helper module
- Exact bounded formula for `dice_semantic_warning_penalty`, as long as it remains additive and capped
- Whether “applicable” typed fields are expressed through helper predicates or inline lane checks

</decisions>

<specifics>
## Specific Ideas

- Internal and DICE may stay different at generation time, but not at typed recommendation contract time.
- Heuristic fallback is provenance, not a free contender pass.
- A DICE candidate can be visible without being rankable.
- Phase 46 should make it obvious whether DICE produced:
  - no candidates
  - candidates but no eligible contenders
  - warning contenders
  - clean contenders

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [generator.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/generator.py): internal lane canonical action builder, feasibility/constraint flow, validity annotation, execution modeling, trajectory, and offer annotation
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py): DICE plan construction seam via `_dice_plan_record(...)`, candidate-pool assembly, metrics summary, and artifact serialization
- [recommendation_validity.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/recommendation_validity.py): canonical validity taxonomy and plan/action annotation layer; must be consumed, not redesigned
- [dice_baseline.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/dice_baseline.py): DICE backend, heuristic fallback, and method-attempt telemetry seam
- [planner.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/planner.py): consumes contender sets after Phase 45 hard-stop; Phase 46 should gate DICE eligibility before this chooser
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py): collection metrics, source-mix summaries, and additive rerun-proof surface

### Established Patterns
- Recommendation validity remains a lane-agnostic truth owned by Phase 42.5.
- Winner hard-stop remains chooser-owned and lane-agnostic from Phase 45.
- Raw summary and flat metrics continue to be the canonical artifact truth that consumer surfaces mirror later.
- Candidate diagnostics can be wider than the actual planner contender set.

### Integration Points
- `_dice_plan_record(...)` should stop building a semi-independent action contract and instead converge onto shared normalization
- DICE candidate generation should annotate lane-specific quality before planner contention
- candidate pool assembly should preserve DICE diagnostics while splitting out planner-eligible DICE contenders
- collection summary should gain DICE-specific eligibility / invalid / warning / fallback proof

</code_context>

<deferred>
## Deferred Ideas

- Winner hard-stop logic stays in Phase 45 and should not be reopened here.
- Selected-surface cross-entity consistency remains Phase 47 scope.
- Operator packet contradiction cleanup remains Phase 48 scope.
- Threshold widening, approval uplift, or DICE competitiveness tuning beyond quality enforcement remains out of scope.

</deferred>

---

*Phase: 46-dice-lane-validity-enforcement*
*Context gathered: 2026-03-26*
