# Phase 37: Portfolio-Level Numeric Impact - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Aggregate the hardened customer-level action, numeric target, feasibility, execution, offer, and narrative truth into portfolio-level business impact. This phase answers:
- how much change is being asked across the cohort
- how realistic that requested change is
- where institution support matters most
- what the execution-aware portfolio payoff actually looks like

This phase does **not** reopen:
- action taxonomy or grouping
- numeric target generation
- feasibility verdict semantics
- difficulty or execution modeling posture
- offer contract semantics
- single-customer narrative or product-surface contracts

</domain>

<decisions>
## Implementation Decisions

### Carry-Forward Decisions From Prior Phases
- Phase 30 remains authoritative for:
  - canonical action semantics
  - `action_family`
  - grouped action identity
  - `business_view` vs `technical_view`
- Phase 31 remains authoritative for:
  - customer-specific numeric targets
  - one primary numeric target per action
  - business-friendly metric identity
  - semantic-sanity-only target generation
- Phase 32 remains authoritative for:
  - feasibility verdicts
  - clipped vs repaired vs provisional vs invalid semantics
  - `constraint_family`
- Phase 33 remains authoritative for:
  - difficulty truth
  - action-to-group-to-plan execution aggregation
  - approval-dependent plan probability
- Phase 34 remains authoritative for:
  - nested `offer_contract`
  - approval vs acceptance semantics
  - rankable vs provisional offer handling
- Phase 35 remains authoritative for:
  - narrative generation contract
  - business vs technical reveal split
- Phase 36 remains authoritative for:
  - typed product-surface consumption
  - fail-soft UI behavior
  - no UI-side meaning invention

### Headline Portfolio Impact Metrics
- Phase 37 should use exactly four headline business cards:
  - `numeric_plan_coverage`
  - `requested_change_burden`
  - `execution_aware_realization`
  - `portfolio_payoff`
- `requested_change_burden` should not be a raw average of mixed-unit deltas.
- Because unit families differ, the business headline should instead carry:
  - normalized requested change burden
- Raw unit-family distributions should stay out of the default headline layer and move to technical or supporting breakdowns.
- `portfolio_payoff` in the business headline should refer to:
  - execution-aware portfolio payoff
- Nominal payoff should remain available, but only as a secondary comparison layer.
- Institution support should appear in the headline-support layer as:
  - `offer_supported_realization_share`

### Segment Breakdown Priorities
- The primary segment lens for Phase 37 should be:
  - `risk_band`
- The secondary segment lens should be:
  - `recoverability_segment`
- Offer dependency should be surfaced through:
  - `offer_needed_segment`
- Segment review must always produce at least these two executive outputs:
  - `highest payoff segment`
  - `highest burden / lowest realization segment`
- Segment reporting should stay executive and strategy-oriented rather than devolving into raw slice dumps.

### Execution-Aware vs Nominal Portfolio Aggregation
- The canonical portfolio payoff pair is locked as:
  - `nominal_portfolio_payoff`
  - `execution_aware_portfolio_payoff`
- The primary truth for product and proof reading is:
  - `execution_aware_portfolio_payoff`
- The difference between nominal and execution-aware portfolio payoff should be first-class and explicitly named:
  - `realization_gap`
- `realization_gap` should live as a supporting metric directly under the headline set.
- Requested change burden remains its own separate headline metric.
- The efficiency view of that burden should be carried as a second-layer metric:
  - `payoff_per_unit_burden`
- Offer-supported payoff should stay explicitly split as:
  - `nominal_offer_supported_payoff`
  - `realized_offer_supported_payoff`
- In default business reading, the institution-support story should emphasize:
  - `realized_offer_supported_payoff`

### Business vs Technical Visibility Of Portfolio Truth
- The default business portfolio view should show these four headline metrics:
  - `numeric_plan_coverage`
  - `requested_change_burden`
  - `execution_aware_realization`
  - `execution_aware_portfolio_payoff`
- The default business portfolio view should also carry these supporting metrics:
  - `realization_gap`
  - `offer_supported_realization_share`
- Business-facing segment output should stay at executive-insight level rather than full table level.
- The default business segment view should focus on:
  - `highest payoff segment`
  - `highest burden / lowest realization segment`
  - `offer-dependent segment`
- The technical layer should remain fully transparent and include:
  - raw unit-family distributions
  - full segment-by-segment breakdowns
  - nominal vs execution-aware full aggregates
  - offer-supported nominal vs realized splits
  - payoff-per-unit-burden tables
  - metric components or formulas needed for auditability
- The most important product-reading principle for this phase is:
  - more honest than impressive
- If requested change is heavy, realization is weak, or payoff is narrower than nominal uplift suggests, the phase should surface that directly rather than smoothing it away.

### Claude's Discretion
- Exact formulas for:
  - normalized requested change burden
  - execution-aware realization
  - payoff-per-unit-burden
  - nominal vs realized offer-supported payoff
- Exact artifact names and file layouts, as long as:
  - the locked canonical metrics remain explicit
  - business and technical layers remain clearly separated
  - execution-aware truth remains primary
- Exact segment-breakdown table schemas, as long as:
  - `risk_band`, `recoverability_segment`, and `offer_needed_segment` remain first-class
  - highest-payoff and highest-burden/lowest-realization outputs remain visible

</decisions>

<specifics>
## Specific Ideas

- The user does not want Phase 37 to become another generic coverage audit.
- The portfolio question is now:
  - how much numeric change are we asking from the cohort
  - how much of that is realistically realizable
  - how much payoff survives execution truth
  - where institution support is carrying the result
- The user wants mixed-unit recommendations to be explainable at the portfolio level without collapsing into unreadable raw metric dumps.
- The user wants business reading to stay concise and honest, while the technical layer remains fully inspectable.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`
  - already aggregates full-cohort coverage, reality-gap, offer, trajectory, and behavior truth
  - already renders portfolio review copy and summary artifacts
  - is the natural seam for adding portfolio-level numeric impact summaries without reopening single-customer contracts
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - already writes execution, offer, and portfolio validation tables into run artifacts
  - already carries fields such as:
    - `best_plan_execution_probability`
    - `best_mean_group_difficulty_score`
    - `best_combined_plan_realization_probability`
    - offer summary fields
  - is the likely seam for emitting the new numeric-impact breakdown artifacts
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already aggregates seed-level portfolio validation, execution, offer, and segment summaries
  - is the likely seam for suite-level numeric impact rollups
- `credit-coach/src/credit_coach/ops/kpi_contract.py`
  - already renders behavior-aware and offer-aware business review summaries
  - can absorb the new Phase 37 headline/supporting metric story without becoming the source of truth

### Established Patterns
- Machine-readable portfolio artifacts remain the source of truth; markdown and review copy are derived.
- Execution-aware evidence remains more important than nominal-only upside when product or proof claims are made.
- Segment reporting should yield business strategy insight rather than table-heavy reporting.
- Product-facing summaries should remain concise, while technical exports stay fully inspectable.

### Current Gaps Visible In Code
- Existing portfolio artifacts already speak about:
  - coverage
  - reality-gap
  - execution
  - offer optimization
  - trajectory
- But there is not yet a locked portfolio truth family for:
  - normalized requested change burden
  - nominal vs execution-aware portfolio payoff as a canonical pair
  - realization gap as a first-class metric
  - offer-supported realized payoff
  - payoff-per-unit-burden
- This means Phase 37 should extend current portfolio seams rather than replace them.

### Integration Points
- Primary engine seams for Phase 37:
  - `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`
  - `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - `credit-coach/src/credit_coach/ops/kpi_contract.py`
- Likely downstream consumers:
  - proof-facing summaries
  - portfolio review markdown
  - future calibration and pilot artifacts

</code_context>

<deferred>
## Deferred Ideas

- Calibration thresholds and realism validation for these new portfolio metrics belong to Phase 38.
- Institution-specific deployment or pilot packaging of these portfolio outputs belongs to Phase 39.
- Any new website redesign or customer-surface change remains out of scope; Phase 36 already owns the surface contract.

</deferred>

---
*Phase: 37-portfolio-level-numeric-impact*
*Context gathered: 2026-03-22*
