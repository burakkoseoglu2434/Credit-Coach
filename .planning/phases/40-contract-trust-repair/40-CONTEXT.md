# Phase 40: Contract & Trust Repair - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Make raw customer artifacts and flat review artifacts trustworthy enough to carry final decision truth without null leaks, parity drift, or zero-step ambiguity.

Phase 40 is strictly about:
- contract integrity
- null-free decision-carrying fields
- raw-to-flat parity
- zero-step hard enforcement
- contract health reporting
- validation and fail-fast behavior

Phase 40 does **not** define:
- approval vs conditional thresholds
- readiness policy semantics beyond contract-safe carriage
- confidence policy tuning
- operator narrative quality
- cohort calibration strategy
- planner ranking redesign

Those remain in later phases, especially:
- Phase 40.5 for deterministic decision ownership
- Phase 41 for cohort calibration
- Phase 43 for operator review packs

</domain>

<decisions>
## Implementation Decisions

### Exact Scope Of Phase 40
- Phase 40 owns the artifact contract, not the full decision policy.
- The deliverable is a null-free, parity-safe artifact surface that can safely carry external and internal decision fields once Phase 40.5 finalizes policy semantics.
- Phase 40 may apply only **contract-safe status repair**, not new approval logic.
- Allowed Phase 40 status behavior:
  - preserve legacy winner status where safe
  - hide internal-only `NEEDS_REVIEW` from business-visible outputs
  - enforce zero-step -> `REJECTED`
  - map contract inconsistency or missing critical truth to:
    - internal: `NEEDS_REVIEW`
    - external: `CONDITIONAL`
- Phase 40 must not redesign the scoring or threshold logic for normal `APPROVED` and `CONDITIONAL` outcomes. That belongs to Phase 40.5.

### Required Schema And Contract Changes For Raw Customer Artifacts
- `customer_roadmap.json` remains the canonical raw single-customer artifact.
- Decision-carrying fields should have one canonical home: `summary`.
- `summary` is the source of truth.
- `contract_health` is a derived view only and must never become a competing decision source.
- Required null-free `summary` fields for every raw roadmap:
  - `decision_status`
  - `decision_status_internal`
  - `credit_readiness_stage`
  - `plan_execution_probability`
  - `approval_dependent_plan_probability`
  - `offer_acceptance_probability`
  - `combined_plan_realization_probability`
  - `best_action_count`
  - `zero_step_flag`
  - `raw_contract_pass`
  - `parity_pass`
  - `data_issue_flag`
  - `data_issue_codes`
- Existing top-level legacy fields stay for compatibility:
  - `best_status`
  - `best_plan_id`
  - `best_plan_source`
  - `trajectory_status`
- Top-level raw artifact should add a small `contract_health` block so humans do not need to infer trust from nested fields.
- `contract_health` minimum raw fields:
  - `raw_contract_pass`
  - `parity_pass`
  - `critical_field_null_count`
  - `missing_checkpoint_status_count`
  - `zero_step_flag`
  - `data_issue_flag`
  - `data_issue_codes`
- Raw checkpoint contract is mandatory for every emitted checkpoint:
  - `checkpoint_id`
  - `week`
  - `checkpoint_label`
  - `predicted_pd`
  - `gate_pass_estimate`
  - `status`
  - `trajectory_jump_flag`
  - `non_monotonic_flag`
  - `checkpoint_inconsistency_flag`
- Raw checkpoint `status` can never be missing or empty after Phase 40.
- Raw roadmap may contain zero steps only when the customer is contract-rejected as `NO_PATH`.

### Contract-Safe Fallback Rules
- Phase 40 must fill decision-carrying fields deterministically even before Phase 40.5 ships the full policy layer.
- Canonical external status fallback:
  - if `zero_step_flag == 1` -> `decision_status = REJECTED`
  - else if `data_issue_flag == 1` -> `decision_status = CONDITIONAL`
  - else -> `decision_status = best_status` legacy passthrough
- Canonical internal status fallback:
  - if `zero_step_flag == 1` -> `decision_status_internal = REJECTED`
  - else if severe inconsistency or parity failure exists -> `decision_status_internal = NEEDS_REVIEW`
  - else -> `decision_status_internal = decision_status`
- Canonical probability fallback rules:
  - if `combined_plan_realization_probability` is null -> set it to `plan_execution_probability`
  - if `approval_dependent_plan_probability` is null -> set it to `plan_execution_probability`
  - if `offer_acceptance_probability` is null -> set it to `0.0`
- Canonical zero-step rule:
  - `zero_step_flag = (best_action_count == 0)`
- Canonical checkpoint fallback:
  - if `checkpoint.status` is null or empty -> set `checkpoint.status = "unknown"` and mark `data_issue_flag = 1`

### Required Schema And Contract Changes For Flat Review Artifacts
- `customer_metrics.csv` becomes the canonical flat customer-level review table.
- Required new flat columns:
  - `decision_status`
  - `decision_status_internal`
  - `credit_readiness_stage`
  - `plan_execution_probability`
  - `approval_dependent_plan_probability`
  - `offer_acceptance_probability`
  - `combined_plan_realization_probability`
  - `best_action_count`
  - `zero_step_flag`
  - `raw_contract_pass`
  - `parity_pass`
  - `data_issue_flag`
  - `data_issue_codes_json`
  - `critical_field_null_count`
  - `missing_checkpoint_status_count`
  - `checkpoint_status_4w`
  - `checkpoint_status_12w`
  - `checkpoint_status_24w`
- Existing legacy flat columns remain during Phase 40 for backward compatibility:
  - `best_status`
  - `best_plan_source`
  - `trajectory_pd_4w`
  - `trajectory_gate_pass_4w`
  - `trajectory_gate_pass_12w`
  - `trajectory_gate_pass_24w`
- `customer_plans.csv` should add:
  - `plan_step_count`
  - `selected_best_flag`
  - `plan_contract_pass`
  so zero-step and empty-winner issues can be audited at plan level.
- `customer_roadmap_steps.csv` remains the best-plan step table and stays empty only for `zero_step_flag = 1` rejected customers.
- `collection_manifest.json` must add contract-health rollups:
  - `contract_pass_count`
  - `contract_fail_count`
  - `raw_flat_mismatch_count`
  - `zero_step_rejected_count`
  - `data_issue_conditional_count`
- `collection_summary.md` must add a first-class `Contract Health` section.

### Raw To Flat Parity Rules
- Parity is enforced per customer between:
  - raw `customer_roadmap.json`
  - raw `metrics.json`
  - flat `customer_metrics.csv`
  - raw `customer_roadmap_steps.csv`
  - flat `customer_roadmap_steps.csv`
- Required raw-vs-flat equality rules:
  - raw `customer_id` == flat `customer_id`
  - raw `best_plan_id` == flat `best_plan_id`
  - raw `best_plan_source` == flat `best_plan_source`
  - raw `summary.decision_status` == flat `decision_status`
  - raw `summary.decision_status_internal` == flat `decision_status_internal`
  - raw `summary.credit_readiness_stage` == flat `credit_readiness_stage`
  - raw `summary.plan_execution_probability` == flat `plan_execution_probability`
  - raw `summary.approval_dependent_plan_probability` == flat `approval_dependent_plan_probability`
  - raw `summary.offer_acceptance_probability` == flat `offer_acceptance_probability`
  - raw `summary.combined_plan_realization_probability` == flat `combined_plan_realization_probability`
  - raw computed `best_action_count` == flat `best_action_count`
  - raw checkpoint statuses for `4w`, `12w`, `24w` == flat checkpoint status columns
  - raw `zero_step_flag` == flat `zero_step_flag`
- Raw and flat contract-health booleans must also agree:
  - `raw_contract_pass`
  - `parity_pass`
  - `data_issue_flag`
- Parity failure is classified, not silently ignored.
- Parity comparison must use normalized numeric tolerance only where float formatting differs; all statuses and flags require exact match.
- Global float parity tolerance is fixed at `1e-6`.
- Parity failure behavior is fixed:
  - `parity_pass = 0`
  - `data_issue_flag = 1`
  - `decision_status_internal = NEEDS_REVIEW`
  - `decision_status = CONDITIONAL`
  - `data_issue_codes += ["parity_mismatch"]`

### Global Zero-Step Enforcement Rules
- Zero-step is defined as:
  - `best_action_count == 0`
  - and flat `customer_roadmap_steps.csv` has zero rows for that best customer
- Global rule:
  - if `best_action_count == 0`
  - then external decision must be `REJECTED`
  - internal decision must be `REJECTED`
  - `zero_step_flag = 1`
  - `rejection_type = NO_PATH` should be carried if the schema already supports it, otherwise Phase 40 must emit `data_issue_codes += ["zero_step_no_path"]` as a bridge until Phase 40.5
- No zero-step customer may serialize as:
  - `APPROVED`
  - `CONDITIONAL`
  - external data-issue fallback
- Zero-step rejection is a hard invariant and should be validated before raw or flat write completes.

### Contract Health Metrics
- Phase 40 should make trust measurable at customer level and collection level.
- Required customer-level metrics:
  - `critical_field_null_count`
  - `missing_checkpoint_status_count`
  - `zero_step_flag`
  - `raw_contract_pass`
  - `parity_pass`
  - `data_issue_flag`
  - `data_issue_codes`
- Required collection-level rollups:
  - `critical_field_null_rate`
  - `raw_contract_pass_rate`
  - `raw_flat_mismatch_count`
  - `missing_checkpoint_status_rate`
  - `zero_step_rejected_count`
  - `data_issue_conditional_count`
  - `summary_field_completion_rate`
- `collection_summary.md` should show the rollups in business-readable form.
- `collection_manifest.json` should carry the same metrics in machine-readable form.
- `raw_contract_pass` is defined as:
  - `critical_field_null_count == 0`
  - and `missing_checkpoint_status_count == 0`
- `data_issue_flag = 1` if any of the following hold:
  - `critical_field_null_count > 0`
  - `missing_checkpoint_status_count > 0`
  - `parity_pass == 0`
- Canonical `data_issue_codes` enum set for Phase 40:
  - `missing_required_field`
  - `checkpoint_status_missing`
  - `parity_mismatch`
  - `zero_step_no_path`

### Validation And Fail-Fast Rules
- Validation should run in one fixed nine-step order:
  1. normalize raw roadmap
  2. fill null defaults
  3. compute `zero_step_flag`
  4. compute `data_issue_flag`
  5. compute internal decision
  6. compute external decision
  7. build flat row
  8. run raw-vs-flat parity validation
  9. finalize `contract_health`
- Raw artifact normalization must fail fast if mandatory roadmap structure is missing:
  - no `summary`
  - malformed JSON or malformed roadmap object
  - malformed checkpoints
  - missing `customer_id`
  - missing `best_plan_id`
- After normalization, remaining contract issues should be classified, not dropped.
- Per-customer validation behavior:
  - missing or mismatched critical fields ->
    - internal `NEEDS_REVIEW`
    - external `CONDITIONAL`
    - `data_issue_flag = 1`
  - zero-step ->
    - internal `REJECTED`
    - external `REJECTED`
  - valid null-free parity-safe record ->
    - `raw_contract_pass = 1`
    - `parity_pass = 1`
- Collection runner should not abort the entire 50-customer run because one customer has a contract issue.
- Single-customer artifact generation should fail fast if a contract-safe record cannot be produced after normalization.
- Tests must fail on:
  - top-level or summary null leaks in required fields
  - missing checkpoint status
  - zero-step non-rejected serialization
  - raw-vs-flat parity drift

### Acceptance Criteria
- `customer_roadmap.json` summary is null-free for all required decision-carrying fields.
- `customer_metrics.csv` carries the same decision-critical truth as raw roadmap summary.
- `combined_plan_realization_probability`, `approval_dependent_plan_probability`, and `offer_acceptance_probability` never serialize as null after fallback normalization.
- checkpoint `status` is present for every emitted checkpoint.
- all zero-step customers serialize as `REJECTED`.
- internal-only `NEEDS_REVIEW` never leaks into business-visible flat outputs.
- raw-vs-flat mismatches are classified and counted, not silently tolerated.
- collection summary and manifest expose contract health clearly enough to diagnose trust failures in one read.

### Outputs And Artifacts
- Updated raw single-customer artifact contract:
  - `customer_roadmap.json`
  - `metrics.json`
  - `customer_roadmap_steps.csv`
- Updated flat collection artifact contract:
  - `customer_metrics.csv`
  - `customer_plans.csv`
  - `customer_roadmap_steps.csv`
  - `collection_manifest.json`
  - `collection_summary.md`
- Updated contract/parity tests:
  - single-customer artifact tests
  - collection artifact tests
  - zero-step enforcement regression tests

### Recommended Implementation Order
- First, add one shared `contract_normalize()` seam for:
  - null fill
  - canonical fallback values
  - zero-step detection
  - data issue flagging
  - internal/external contract-safe status fallback
- Second, lock one shared contract definition for required raw and flat fields so `run_recourse` and collection code stop drifting independently.
- Second, normalize `_build_customer_roadmap(...)` and `_build_customer_metrics_summary(...)` to emit the full null-free summary plus checkpoint-status fields.
- Third, extend `write_customer_artifact_bundle(...)` and collector augmentation code so raw and flat artifacts carry the same decision-critical truth.
- Fourth, add zero-step detection and hard rejection enforcement before artifacts are written.
- Fifth, add a reusable raw-vs-flat parity validator and contract-health calculator used by both single-customer and collection outputs.
- Sixth, expand `collection_manifest.json` and `collection_summary.md` with contract-health metrics.
- Seventh, backfill regression tests around:
  - current null top-level raw roadmap behavior
  - missing combined realization values
  - zero-step winners
  - parity mismatches

### Claude's Discretion
- Exact helper/function names for normalization and parity validation
- Whether contract-health data lives only in `summary`, only in `contract_health`, or both, as long as one canonical source is declared and parity remains testable
- Exact JSON shape of `data_issue_codes` payload as long as it uses the locked canonical enum values
- Exact severity threshold that separates ordinary data issues from severe inconsistency as long as parity failure always counts as severe

</decisions>

<specifics>
## Specific Ideas

- The user explicitly wants Phase 40 to stay narrow:
  - fix contract trust
  - do not redesign approval logic
  - do not spill operator UX or calibration concerns into this phase
- Current real artifact evidence from the 50-customer collection run shows:
  - top-level raw roadmap fields such as `decision_status`, `credit_readiness_stage`, `plan_execution_probability`, `approval_dependent_plan_probability`, and `combined_plan_realization_probability` are missing in `50/50` raw files
  - the canonical `summary` block already carries `decision_status`, `credit_readiness_stage`, and `plan_execution_probability`
  - `approval_dependent_plan_probability` and `combined_plan_realization_probability` are still null in `50/50` summary blocks
  - checkpoint `status` is already present in the sampled raw files and should be preserved as required truth
  - zero-step best outcomes still exist (`19/50`) and must be classified as hard rejections
- Business trust rule for this phase:
  - system inconsistency is a data issue, not a customer rejection
  - therefore inconsistency maps to external `CONDITIONAL`, not `REJECTED`
- This phase should leave Phase 40.5 a clean seam:
  - raw and flat artifacts already trustworthy
  - later decision thresholds can be added without reworking serialization

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py)
  - `_build_customer_roadmap(...)` already computes the canonical `summary` block and checkpoint structure
  - `_build_customer_metrics_summary(...)` is the current flat customer metrics seam
  - `write_customer_artifact_bundle(...)` already writes the raw bundle set and is the cleanest place to enforce bundle validation
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py)
  - `_augment_metrics_row(...)` currently mirrors only part of roadmap summary into flat metrics
  - `_collection_summary_markdown(...)` is the seam for contract-health summary output
  - manifest generation already exists and can absorb machine-readable contract-health counters
- [schema.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py)
  - still carries legacy `decision_status` semantics including `NEEDS_REVIEW | UNKNOWN`
  - is the right place to prepare contract-safe status fields without yet shipping the final Phase 40.5 policy
- [test_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_customer_artifact_collection.py)
  - already proves raw and flat files are emitted
  - is the natural regression seam for parity, null-free fields, and contract-health assertions
- [test_recourse_redesign.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_recourse_redesign.py)
  - already exercises roadmap-building behavior
  - should own the single-customer raw artifact contract assertions
- [live-demo.ts](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/server/services/live-demo.ts)
  - already consumes raw roadmap summary fields such as `decision_status`, `credit_readiness_stage`, and realization probabilities
  - currently falls back to raw `best_status`, which is evidence that the raw contract is not yet clean enough
- [demo-schema.ts](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/shared/demo-schema.ts)
  - already models `decision_status` and `credit_readiness_stage` on the consumer side
  - indicates the upstream producer contract should become less optional, not more ad hoc

### Established Patterns
- v2.0 already established:
  - engine-owned artifact truth
  - raw per-customer bundle plus flat collection review tables
  - business-safe summary plus deeper technical reveal
- Collection review already uses one joined customer key surface:
  - `collection_run_id`
  - `batch_index`
  - `source_row_index`
  - `customer_id`
- The current raw roadmap contract already prefers a nested `summary` block for business-facing key fields.
- The current website consumer still compensates for weak upstream contract by inferring or falling back. Phase 40 should reduce that need at the source.

### Integration Points
- Primary producer seams:
  - `credit-coach/src/credit_coach/cli/run_recourse.py`
  - `credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py`
- Primary contract seam:
  - `credit-coach/src/credit_coach/data/schema.py`
- Primary regression seams:
  - `credit-coach/tests/test_recourse_redesign.py`
  - `credit-coach/tests/test_customer_artifact_collection.py`
- Important downstream consumers to keep compatible:
  - `credit-coach-website/server/services/live-demo.ts`
  - `credit-coach-website/shared/demo-schema.ts`

</code_context>

<deferred>
## Deferred Ideas

- Deterministic thresholding for normal `APPROVED` vs `CONDITIONAL` decisions belongs to Phase 40.5.
- `decision_confidence`, `expected_readiness`, `conditional_type`, and full rejection subtype policy belong to Phase 40.5, except where Phase 40 needs bridge fields for zero-step or data-issue classification.
- Mixed-cohort calibration and threshold tuning belong to Phase 41.
- Operator packet wording, downside risk copy, and review pack UX belong to Phase 43.
- Source-mix competitiveness and planner-quality recovery belong to Phase 42.
- Policy-version reruns and institution-facing pilot docs belong to Phase 44.

</deferred>

---
*Phase: 40-contract-trust-repair*
*Context gathered: 2026-03-23*
