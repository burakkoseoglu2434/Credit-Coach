# Phase 44 — Production Pilot Baseline Context

**Last updated:** 2026-03-23
**Status:** Discussed and locked
**Milestone:** `v2.1 Decision Ownership & Pilot-Ready Trust`
**Requirements:** `PROD-01`, `PROD-02`

<domain>
## Phase Boundary

Phase 44 does **not** redesign:

- Phase 40 contract normalization or parity-safe artifact ownership
- Phase 40.5 deterministic decision ownership or decision thresholds
- Phase 41 cohort semantics, funnel math, or calibration math
- Phase 43 operator packet semantics
- Phase 42 planner-quality and source-mix logic

Phase 44 **does** own:

- rerunnable production-pilot orchestration over existing runners
- declared proof-refresh cadence and version-comparison discipline
- artifact QA gates and release-smoke packaging for pilot refreshes
- institution policy versus institution offer config separation
- compliance-adjacent institution-facing explanation packaging
- honest, bounded pilot story guidance for proof surfaces

Guardrails:

- new orchestrator, no new engine
- existing decision payload remains the single truth owner
- calibration artifacts remain read-only measurement outputs
- operator packets remain derived internal-review artifacts
- live integrations, automation scheduling, and self-serve pilot tooling stay out of scope

</domain>

<decisions>
## Implementation Decisions

### 1. Rerun Cadence And Proof Refresh Contract

- Phase 44 should add a new orchestration CLI over existing runners:
  - `run_pilot_baseline_refresh`
- The orchestrator should sequence existing lanes rather than inventing new decision logic:
  - collection run
  - calibration and operator artifacts
  - pilot package refresh
  - smoke and QA
  - version comparison
- Refresh posture is:
  - `operator-triggered with declared cadence contract`
- Canonical cadence modes:
  - `pre_pilot`
  - `weekly_during_pilot`
  - `pre_readout`
- Cadence must be visible in both machine-readable and human-readable outputs.
- Canonical comparison baseline:
  - current run vs previous approved pilot-baseline run with the same institution profile
- Required comparison metadata:
  - `reference_run_id`
  - `reference_label`
- Guardrail:
  - if no approved prior baseline exists, comparison must fall back to explicit reference only and be marked non-canonical
- Minimum refresh outputs:
  - `pilot_refresh_manifest.json`
  - `pilot_refresh_summary.md`
  - `policy_version_comparison.csv`
  - `policy_version_comparison.md`
  - `artifact_qa_summary.json`
  - `release_smoke_summary.json`
- Optional but preferred:
  - `refresh_context.json`
  - carrying cadence mode, institution profile, reference run, policy version, and invoked runners

### 2. Artifact QA Gate And Release / Portfolio Smoke

- Phase 44 should add a separate pilot artifact QA runner:
  - `run_pilot_artifact_qa.py`
- Existing `run_production_smoke.py` remains the portfolio / KPI / fairness / telemetry / release smoke lane.
- The new QA gate is the pilot trust fence and must cover:
  - completeness
  - contract and trust
  - packaging integrity
  - calibration and operator completeness
- Completeness checks should include:
  - required artifacts present
  - `raw/`, `flat/`, `calibration/`, and operator packet outputs present
- Contract / trust checks should include:
  - critical field null rate is `0`
  - raw / flat parity integrity
  - decision-status consistency
  - no leaked internal-only states such as `NEEDS_REVIEW`
- Packaging integrity checks should include:
  - manifest paths resolve to real files
  - schema drift flags
  - policy-version consistency
  - cohort metadata consistency
- Calibration / operator completeness checks should include:
  - funnel and readiness artifacts present
  - calibration subtree complete
  - operator packet coverage is effectively `100%`
- QA result contract is three-level:
  - `PASS`
  - `DEGRADED`
  - `FAIL`
- Fail behavior:
  - `FAIL` blocks pilot baseline acceptance
  - `DEGRADED` remains usable but must be visibly called out in refresh summary
- Final orchestrator summary must report separate lanes:
  - `portfolio_smoke_status`
  - `artifact_qa_status`

### 3. Institution Policy Vs Offer Config Separation

- Phase 44 should add thin YAML overlay contracts rather than replacing existing configs.
- Canonical overlays:
  - `institution_policy.yaml`
  - `institution_offer.yaml`
  - optional `pilot_profile.yaml`
- Existing base configs remain intact.
- `institution_policy` owns:
  - decision and usage constraints
  - pilot traffic posture
  - allowed cohort and refresh posture
  - explanation-pack wording guardrails
- `institution_offer` owns:
  - enabled offer families
  - offer maturity defaults
  - approval dependency flags
  - institution-side action availability
- Runtime config precedence is fixed:
  1. base configs
  2. institution policy / offer overlays
  3. pilot bundle context
  4. explicit CLI overrides
- Every resolved runtime config should be materialized into the run manifest so reruns are reproducible and auditable.
- Scope guardrail:
  - config separation remains limited to local YAML overlays, manifest provenance, and runbook clarity
  - no live config sync, CRM/LOS binding, or runtime API config fetch

### 4. Compliance-Adjacent Explanation Pack And Honest Proof Surface

- Phase 44 should add a new institution-facing explanation artifact:
  - `decision_explanation_pack.json`
- The artifact is:
  - institution-facing
  - audit-friendly
  - non-legal
  - reproducible
- Minimum explanation-pack fields:
  - `decision_id`
  - `customer_id` or institution-safe customer reference
  - `decision_outcome`
  - `external_decision_only`
  - `one_line_decision_reason`
  - `structured_numeric_drivers`
  - `driver_methodology_note`
  - `upgrade_condition`
  - `expected_readiness`
  - `adverse_action_friendly_reasons`
  - `policy_version`
  - `policy_effective_at`
  - `artifact_generated_at`
  - `contract_version`
  - `qa_status`
  - `qa_stamp`
  - `human_review_required`
  - `disclaimer`
- Explanation-pack blocks should read as:
  - decision summary
  - driver summary
  - improvement path
  - adverse-action-compatible reasons
  - governance
  - boundary statement
- Design rule:
  - explanation pack should answer why this decision happened without dumping internal policy mechanics
- Relationship to operator packet is fixed:
  - shared truth, different audience
  - truth owner = Phase 40.5 decision payload
  - operator packet = internal lens
  - explanation pack = external-safe lens
- Mandatory consistency rules:
  - operator packet and explanation pack must share the same `decision_id`
  - operator packet and explanation pack must share the same `policy_version`
  - no reason drift across derived artifacts
  - no upgrade-condition drift across derived artifacts
  - no readiness drift across derived artifacts
- Proof-surface rule is:
  - proof without leakage
- Proof surfaces may show:
  - pilot refresh completed
  - policy version
  - package QA status
  - portfolio smoke status
  - artifact completeness
  - generation timestamp
  - contract / schema version
  - institution overlay availability
  - `safe_to_pilot`
  - `pilot_watchlist`
- Proof surfaces must not show:
  - `NEEDS_REVIEW`
  - internal review queue state
  - raw candidate tables
  - raw policy trace
  - internal QA failure dumps
  - debug metadata
  - reviewer-only notes
- Honest pilot story tone is:
  - controlled
  - governed
  - repeatable
  - versioned
  - reviewable
  - bounded
- Safe claims:
  - deterministic decisions
  - repeatable pilot refresh
  - QA-gated packages
  - institution-configurable overlays
- Explicit non-claims:
  - not live-integrated
  - not self-serve
  - not compliance automation
  - not autonomous adjudication
  - not institution policy replacement

### Claude's Discretion

- Exact file naming for auxiliary refresh metadata beyond the locked minimum set
- Exact warning wording for `DEGRADED` statuses
- Exact rendering/layout choices for proof-surface status blocks so long as they honor the locked vocabulary and leakage guardrails

</decisions>

<specifics>
## Specific Ideas

- The right posture is: `new orchestrator, no new engine`
- Cadence should be declared but not automated in this phase
- `PASS / DEGRADED / FAIL` is the preferred QA vocabulary
- `institution_policy` and `institution_offer` should stay separate because usage posture and offer-carrying capacity are different truths
- Explanation pack should be an audience-specific projection of the same decision snapshot, not a simplified copy that can drift
- Honest pilot story should sound like:
  - "controlled pilot baseline"
  - not "production-grade autonomous decisioning"

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets

- [run_pilot_integration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_integration.py): existing pilot package builder and mirrored artifact lane
- [run_production_smoke.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_production_smoke.py): existing portfolio / KPI / release smoke runner
- [release_decision.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/release_decision.py): existing release decision, guardrail, and rollout posture helpers
- [contracts.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/pilot/contracts.py): current pilot input and pilot package contract models
- [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py): current policy-version comparison and calibration artifacts
- [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py): current derived operator packet lane
- [policy/engine.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/policy/engine.py): adverse-action-friendly reason payload seam

### Established Patterns

- Phase 40.5 decision payload is the single truth owner for business-visible and internal decisions
- Phase 41 calibration outputs are additive, same-run-root artifacts and must stay measurement-only
- Phase 43 operator packets are derived views and must not invent new truth
- Phase 42 kept provenance explicit with source fields instead of inference-heavy consumer logic
- Phase 39 already established export-first pilot package discipline and guarded pilot posture

### Integration Points

- New production-pilot orchestrator should compose existing collection, pilot-package, smoke, and QA lanes
- New QA runner should validate artifacts after collection and package generation, before refresh is treated as acceptable
- New institution overlays should feed orchestrator runtime config resolution and be written into refresh manifests
- New explanation pack should derive from decision payload plus existing adverse-action and operator-review ingredients
- Proof-surface guidance should align engine docs and website docs without creating a parallel website-only pilot truth layer

</code_context>

<deferred>
## Deferred Ideas

- live institution config sync
- CRM / LOS / core banking integrations
- scheduled automation of refresh cadence
- self-serve pilot workspace
- legal or compliance opinion automation
- autonomous policy rollout or autonomous adjudication

</deferred>

---

*Phase: 44-production-pilot-baseline*
*Context gathered: 2026-03-23*
