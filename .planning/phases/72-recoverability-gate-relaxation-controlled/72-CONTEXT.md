# Phase 72: Recoverability Gate Relaxation (Controlled) - Context

**Gathered:** 2026-04-18  
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 72 introduces a safer intermediate recommendation tier (`assisted_full`) that reduces empty-state overuse by surfacing **already-existing latent value** for policy-suppressed customers, while preserving all trust/safety guarantees.

This phase owns:
- a single, controlled policy unlock that routes a subset of customers from `limited` → `assisted_full`
- surfacing exactly **one** minimal, safe, **customer-only** action in `assisted_full`
- explicit provenance for why each customer is `full`, `assisted_full`, or `limited`
- W2a baseline vs controlled-intervention comparison (coverage, empty-state, trust deltas, action diversity, segment-level uplift)

This phase does not own:
- new intelligence, new action generators, or model retraining
- threshold redesign (no tau/policy redesign)
- ranking changes (keep winner selection and ordering unchanged)
- multi-action surfacing (Phase 73)
- multi-step/sequential plan surfacing (Phase 74)
- institution-assisted actions in Wave 1 (defer; can be revisited later)

Hard guardrail:
- **Any trust violation is an immediate rollback condition** (invalid winner, surface drift, operator contradictions must remain zero).

</domain>

<decisions>
## Implementation Decisions

### 1) Policy unlock goal: controlled intervention, not new capability
- Key principle: **unlock already-existing value safely**; do not add new intelligence.
- Only one intervention is allowed in this phase: the gate-tier expansion to include `assisted_full` for a subset of otherwise-limited customers.
- Keep selection and ranking unchanged; Phase 72 changes only *routing + minimal surfacing*.

### 2) Eligibility logic for `assisted_full` (Wave 1)
- `assisted_full` eligibility uses **OR logic** between:
  - a threshold-signal proxy (selected-plan `threshold_reach_probability`), and
  - a deterministic gap-closure proxy (`gap_closure_rate`)
- Eligibility thresholds are **data-driven then locked**:
  - scan W2a *pre-gate* distributions to choose thresholds that target ~`7–12%` `assisted_full` share (global denied)
  - once chosen, lock the numeric thresholds for reproducible W2a comparisons
- Recommended gap-closure proxy definition (deterministic, audit-friendly):
  - `gap_closure_rate = best_possible_pd_improvement / max(approval_gap, epsilon)`
  - keep epsilon explicit and stable (avoid divide-by-zero)
- Eligibility should be restricted to **policy-suppressed** customers (those who would otherwise be `limited` under current gate), not to already-`full` customers.

### 3) Surfacing constraints in `assisted_full` (Wave 1)
- **Customer-only only**: exclude `institution_assisted` and exclude hybrid plans in Wave 1.
- Surface exactly **one** minimal action:
  - no multi-step plans
  - no top-k action lists
- Minimal action allowlist (Wave 1):
  - allow `adjust_requested_loan_amount`, plus **one utilization action** (choose from `limit_credit_usage` and/or `reduce_spending`)
  - if multiple allowlisted actions are available, surface the single best/primary one deterministically (no re-ranking changes; pick from the already-selected plan)
- Prevent low-quality/noisy surfacing:
  - if a customer qualifies for `assisted_full` but no allowlisted customer-only action is available in the selected plan, fall back to `limited` (no “forced” actions).

### 4) Provenance and explainability (artifacts)
- Each customer must carry explicit provenance for:
  - `recourse_mode in {full, assisted_full, limited}`
  - why that tier was assigned
- Keep existing gate reason codes stable (do not rewrite the shipped vocabulary), but add **assisted_full provenance**:
  - `assisted_full_reason_codes` (derived, explicit)
  - `assisted_full_thresholds` (the numeric thresholds used)
- Surfaced output must remain interpretable and realistic; avoid implying approval certainty beyond selected-plan evidence.

### 5) Evaluation protocol + success checks
- Mandatory comparison: W2a baseline (no limited-mode surfacing) vs Phase 72 intervention (assisted_full enabled).
- Report at minimum:
  - coverage uplift (absolute + relative)
  - empty-state reduction
  - trust metrics delta (must remain ~0 / exactly 0 for counters)
  - action-type distribution before vs after
  - segment-level uplift (`near_threshold`, `mid_risk`, `hard_denied`)
  - surfaced vs latent alignment improvement (reduced “latent value exists but empty surfaced” gap)
- Rollback condition:
  - any non-zero trust counter (invalid winner, surface drift, operator contradiction) aborts the experiment.

### Claude's Discretion
- The exact numeric threshold values for the first Wave 1 run (after W2a scan), as long as they:
  - target ~`7–12%` assisted_full share, and
  - are locked for reproducibility once chosen
- The exact string taxonomy for `assisted_full_reason_codes`, as long as it is deterministic and auditable.
- Whether the utilization action component is `limit_credit_usage`, `reduce_spending`, or a deterministic preference order across both.

</decisions>

<specifics>
## Specific Ideas

- Phase 72 is explicitly “diagnosis → controlled intervention”:
  - convert policy-suppressed latent value into minimal surfaced value safely
- Wave 1 experiment framing:
  - condition: threshold proxy OR movement proxy (calibrated + locked)
  - action: surface exactly 1 minimal safe action (customer-only; no institution; no multi-step)
  - control: W2a baseline with current limited-mode empty-state behavior

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `credit-coach/src/credit_coach/evaluation/recoverability.py`:
  - `build_recourse_gate(...)` is the current routing switch (`full` vs `limited`) and is the natural policy-unlock seam.
- `credit-coach/src/credit_coach/cli/run_recourse.py`:
  - `_apply_recourse_gate_to_roadmap(...)` rewrites selected truth to empty-state when `recourse_mode == limited`; Phase 72 must preserve this behavior for `limited` and avoid it for `assisted_full`.
- Phase 71 diagnostics:
  - `credit-coach/src/credit_coach/evaluation/coverage_diagnostics.py` and `credit-coach/src/credit_coach/cli/run_v27_coverage_diagnostics.py` provide a derived “policy-suppressed” taxonomy and segment reporting that Phase 72 can use for calibration and evaluation.

### Established Patterns
- “Trust-clean” is a hard invariant:
  - any surfaced intervention must preserve `selected_invalid_winner_count=0`, `selected_surface_drift_count=0`, `operator_packet_contradiction_count=0`.
- Additive artifacts over contract rewrites:
  - Phase 72 should prefer adding provenance fields/artifacts rather than redefining existing canonical CSV contracts.

### Integration Points
- Gate tier expansion: `credit-coach/src/credit_coach/evaluation/recoverability.py` (recourse gate logic and reason codes)
- Surface projection behavior by tier: `credit-coach/src/credit_coach/cli/run_recourse.py` (limited-mode empty-state rewrite vs non-limited projection)
- Evaluation comparability: `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py` (W2a-compatible cohort reruns and artifact emission)

</code_context>

<deferred>
## Deferred Ideas

- Allowing hybrid plans in assisted_full (surface customer step only) — defer until Wave 2 or later if Wave 1 is stable.
- Allowing institution-assisted actions — defer until Wave 2+ once provenance and trust checks are proven stable.
- Multi-action surfacing — Phase 73.
- Multi-step plan surfacing — Phase 74.
- Mid-risk longer-horizon unlock messaging — Phase 75.

</deferred>

---

*Phase: 72-recoverability-gate-relaxation-controlled*  
*Context gathered: 2026-04-18*

