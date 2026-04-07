# Phase 63: Recourse Gating By Recoverability - Context

**Gathered:** 2026-04-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 63 uses the shipped Phase 62 recoverability classifier to gate live recourse behavior in a deterministic, honest, and trust-safe way.

This phase owns:
- the canonical runtime `recourse_mode` contract
- deterministic mapping from `recoverable_flag` to runtime behavior
- the first-wave definition of `full` versus `limited` recourse behavior
- additive runtime and artifact fields needed to make gating auditable
- trust-safe suppression rules so non-recoverable customers do not receive fake actionability

This phase does not own:
- classifier redesign or recoverability-threshold redesign
- planner ranking redesign or movement-score logic (Phase 64)
- narrative redesign or customer-facing copy strategy beyond minimal honesty enforcement (Phase 66)
- new action semantics, new data sources, or model retraining
- any widening of winner-selection or trust contracts from `v2.2` and `v2.4`

Guardrail:
- Phase 63 should prefer honest suppression over optimistic over-generation. If a customer is not recoverable, the runtime should suppress recommendation behavior rather than try to rescue it with a weak or institution-heavy path.

</domain>

<decisions>
## Implementation Decisions

### Canonical recourse modes
- Phase 63 should ship a **2-mode** runtime contract only:
  - `full`
  - `limited`
- Do **not** add a third `informational_only` mode in the first wave.
- `limited` already means:
  - no actionable recourse recommendation is being promoted
  - the system may still expose additive diagnostic truth and informational posture
- To separate runtime behavior from presentation posture, Phase 63 should also add:
  - `recommendation_mode = actionable | informational`
- First-wave mapping:
  - `recourse_mode=full` -> `recommendation_mode=actionable`
  - `recourse_mode=limited` -> `recommendation_mode=informational`

### Deterministic mapping from classifier to mode
- Phase 63 should use a direct, deterministic mapping from the shipped Phase 62 classifier:
  - `recoverable_flag = true` -> `recourse_mode = "full"`
  - `recoverable_flag = false` -> `recourse_mode = "limited"`
- There should be **no exception cases** in the first wave.
- That means all non-recoverable customers route to limited mode, including:
  - `mid_risk` customers
  - hard-blocked customers
  - soft-blocked customers
  - customers with technically interesting but non-rankable or non-threshold-reaching paths
- Rationale:
  - false hope is worse than under-generation
  - the classifier is already deliberately conservative
  - adding exception cases now would create a second recoverability rule disguised as gating
- Denied-customer gating is the intended Phase 63 surface. Non-denied behavior can remain on the existing baseline unless planning proves Phase 63 must touch it for contract consistency.

### What full mode means
- `full` mode should preserve the current shipped `v2.4` / `v2.5` recourse behavior.
- In first wave, `full` mode keeps:
  - internal validated plan generation
  - DICE lane generation
  - rule / institution lane generation
  - current contender filtering and winner selection
  - multi-path generation and grouped path artifacts
  - selected-path rendering
  - current selected-surface, operator packet, and explanation-pack behavior
- Phase 63 should therefore treat `full` mode as:
  - the current default runtime, made explicit
  - not a new capability branch

### What limited mode means
- `limited` mode should suppress broad recommendation generation rather than weaken trust rules.
- First-wave limited mode should:
  - suppress DICE expansion as a recommendation-producing lane
  - suppress institution / rule-lane expansion as a recommendation-producing lane
  - suppress multi-path recommendation generation for customer/operator-facing selected truth
  - suppress selected actionable recommendation promotion
  - suppress institution-heavy or low-realism alternative-path surfacing as customer guidance
- First-wave limited mode should **reuse the existing explicit empty-state contract** from Phases 47 and 48 rather than inventing a soft recommendation state.
- That means limited mode should converge selected-surface behavior onto:
  - `best_plan_id = null`
  - `selected_recommendation_source = "empty_state"`
  - `selected_action_count = 0`
  - customer/operator selected surfaces rendering the already-proven empty-state behavior
- Important distinction:
  - this is a **presentation and promotion suppression rule**, not a claim that the customer has no diagnostic evidence
  - classifier truth, blocker truth, and existing decision/context fields should remain available additively for audits and later narrative work
- If planning chooses to preserve any internal diagnostic candidate computation for analysis, those diagnostics must remain non-selected and non-customer-facing.

### Honesty contract for limited mode
- Limited mode must mean:
  - "not currently recoverable for full recourse"
  - not "there is still a good actionable path if we phrase it softly"
- Phase 63 should therefore avoid inventing a quasi-actionable middle ground.
- Customer and operator surfaces should remain mostly unchanged in this phase **except** where they must stop implying current actionability.
- First-wave honesty rules:
  - reuse the trusted explicit empty-state recommendation behavior
  - do not generate a new customer-facing limited-mode prose system yet
  - keep blocker, classifier, and decision context available in additive fields for auditability
  - defer richer informational coaching and structural-language polish to Phase 66
- If a limited-mode customer still has one technically valid path in raw engine terms, that path should **not** be elevated into the selected recommendation in first wave.
- Any such evidence may remain:
  - audit-only
  - cohort-visible
  - operator-diagnostic
  but not a promoted selected path or actionable recommendation.

### Artifact and schema additions
- Minimum additive field contract for Phase 63:
  - `recourse_mode`
  - `recommendation_mode`
  - `recourse_gate_version`
  - `recourse_gate_reason_codes`
- Gate-reason vocabulary should stay small and routing-oriented:
  - `RECOVERABLE_FULL_MODE`
  - `NOT_RECOVERABLE_LIMITED_MODE`
- Detailed why a customer was gated should continue to come from the existing classifier and signal reasons, not from a second large gating vocabulary.

### Where the new fields should land first
- First propagation targets:
  - runtime roadmap summary
  - synced `metrics_summary`
  - customer artifact collection metrics rows
  - cohort evaluation customer-level outputs
- This gives Phase 63:
  - runtime truth
  - flat artifact truth
  - evaluation-ready truth for later Phase 65 cohort comparisons
- Operator packet and explanation pack may receive the new fields additively in technical/debug sections if that is low-risk, but Phase 63 should not redesign their user-facing wording.

### Interaction with existing selection and empty-state contracts
- Phase 63 should preserve the already-proven empty-state surface behavior instead of introducing a new selected-surface outcome enum.
- In first wave:
  - selected-surface presentation should continue to use the Phase 47 / 48 empty-state path
  - audit distinction between "limited-mode suppression" and "organic no valid winner" should come from the new gate fields, not from a new consumer-facing selected outcome
- This keeps:
  - selected-surface consistency stable
  - operator packet coherence stable
  - explanation-pack drift guards stable

### Trust-contract protection
- Gating must not create:
  - selected-surface drift
  - packet contradictions
  - chooser regressions
  - weird empty-state regressions
- Therefore Phase 63 should:
  - leave chooser, threshold, and planner-quality logic untouched
  - apply gating as an upstream runtime behavior decision, not as a chooser-rule rewrite
  - lean on the already-tested empty-state rendering path for limited mode
  - preserve current behavior for recoverable customers exactly
- Trust proof for this phase must explicitly rerun:
  - winner integrity
  - DICE contender quality
  - selected-surface consistency
  - operator packet coherence

### Deterministic edge-case handling
- `recoverable_flag` is the canonical routing truth for Phase 63. Raw path availability must not override it.
- If `recoverable_flag = true` but downstream generation still produces weak or no valid paths:
  - keep `recourse_mode = "full"`
  - preserve the normal shipped pipeline behavior
  - if chooser still ends with no valid winner, reuse the existing organic empty-state outcome rather than adding a special gated branch
- If `recoverable_flag = false` but raw engine logic can still assemble one technically valid path:
  - keep `recourse_mode = "limited"`
  - do not promote that path into selected truth
  - allow it only in audit or cohort diagnostics if retained at all
- If `threshold_reach_possible = false` but the approval gap is numerically small:
  - do not invent a special exception
  - the shipped classifier outcome still governs routing
- If classifier truth and raw candidate/path availability feel in tension:
  - classifier truth wins for routing
  - candidate/path artifacts remain subordinate evidence, not an alternate gate
- Phase 63 should not introduce a second arbitration layer such as:
  - "limited unless one path looks good"
  - "full if a near-threshold path exists"
  - "informational_only when signals conflict"
- This keeps routing deterministic, auditable, and fail-closed.

### Claude's Discretion
- Exact helper/function boundaries for gate resolution, as long as the mapping remains one deterministic classifier-to-mode seam.
- Whether limited mode suppresses recommendation-producing generation before DICE/rule/path construction or suppresses promotion after a narrower diagnostic pass, as long as customer/operator selected truth remains empty-state and no hopeful path is promoted.
- Exact naming of `recourse_gate_version` and the route-level gate-reason literals, as long as the vocabulary remains small and auditable.

</decisions>

<specifics>
## Specific Ideas

- `limited` is the runtime gate; `informational` is the surface posture.
- Reuse the Phase 47 / 48 explicit empty-state contract instead of inventing an “almost actionable” limited-mode recommendation state.
- Do not add a third runtime mode yet. If future evidence demands a finer split, that can be a later explicit rule change.
- Full mode should feel boring by design: it is just the current trusted runtime made explicit.
- Limited mode should suppress institution-heavy optimism, not wrap it in softer wording.
- If selected truth goes empty in limited mode, that should be because the gate intentionally suppressed promotion, not because the system silently changed its honesty contract.
- One informational path may become viable in a later phase, but it should not be promoted as selected truth in this first-wave gating contract.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py): already centralizes candidate generation, chooser invocation, path construction, selected-surface projection, recoverability attachment, and runtime summary/metrics sync. This is the main Phase 63 gating seam.
- [recoverability.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/recoverability.py): already provides the canonical Phase 62 classifier truth (`recoverable_flag`, classifier reason codes, versioning) that Phase 63 should consume directly rather than reinterpret.
- [planner.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/planner.py): chooser outcomes are currently `selected_valid_winner | no_valid_winner`, which reinforces the first-wave decision to reuse the existing empty-state surface rather than add a third selected-surface outcome.
- [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py): already has decision-state-aware empty-state packet handling and should remain a consumer of summary truth rather than a new gating owner.
- [decision_explanation_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/decision_explanation_pack.py): already drift-checks selected recommendation source and projection version, so Phase 63 should preserve those contracts and let empty-state continue to flow through them.
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py): already flattens summary and selected-surface truth into `customer_metrics.csv`, making it the natural first artifact seam for new gate fields.
- [run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py): already resolves runtime-first classifier truth and writes customer-level cohort outputs, so it is the right first place to emit `recourse_mode` and `recommendation_mode` for later targeted evaluation.

### Established Patterns
- The repo prefers additive fields before deeper surface rewrites.
- Explicit empty-state behavior is already trusted and tested across selected surfaces and operator artifacts.
- Trust-sensitive logic in this codebase is fail-closed; Phase 63 gating should mirror that posture.
- Runtime summary fields are the canonical truth that downstream collection and cohort artifacts consume.
- Later milestone work should consume prior truth contracts rather than introduce parallel surface-specific interpretations.

### Integration Points
- Add one gate-resolution helper near the existing recoverability attachment in `run_recourse.py` so runtime summary derives `recourse_mode` from the shipped classifier at one seam.
- Apply gating before recommendation promotion and selected-path surfacing, without redesigning chooser or threshold logic.
- Reuse `_build_selected_surface_projection(...)` empty-state behavior for limited mode rather than designing a new selected-surface branch.
- Extend runtime summary/metrics sync, collection rows, and cohort customer outputs with the new mode fields first.
- Keep operator packet and explanation pack mostly unchanged, with only additive pass-through or inherited empty-state behavior in Phase 63.

</code_context>

<deferred>
## Deferred Ideas

- Adding a third runtime mode such as `informational_only`
- Promoting one informational path in limited mode as selected truth
- Allowing mid-risk or soft-blocked exception cases back into full mode
- Rich customer-facing limited-mode messaging, structural-language polish, and `narrative_type` changes (Phase 66)
- Movement-aware ranking or threshold-probability scoring changes (Phase 64)
- Any classifier loosening, threshold redesign, model retraining, or new action-type scope

</deferred>

---

*Phase: 63-recourse-gating-by-recoverability*
*Context gathered: 2026-04-07*
