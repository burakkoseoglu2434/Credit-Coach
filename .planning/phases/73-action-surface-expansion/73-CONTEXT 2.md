# Phase 73: Action Surface Expansion - Context

**Gathered:** 2026-06-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 73 moves customers in `recourse_mode=full` from single-action surfacing to **top-k=2 surfaced actions**, when the selected plan offers ≥2 valid actions from distinct action families. The surfaced output must publish action-type distribution metrics so single-family dominance can be detected in cohort evaluation (`SURF-03`).

This phase owns:
- top-k=2 action surfacing for `full`-tier customers (diversity-first selection: keep the existing winner as action #1, fill action #2 from the next-best DISTINCT action family if one exists)
- action-type distribution metrics published in cohort evaluation artifacts
- narrative/output changes needed to represent 2 actions without exceeding selected-plan evidence (`TRUST-04`)

This phase does not own:
- `assisted_full` tier — stays at exactly 1 customer-only action per Phase 72's locked contract (untouched)
- `limited` tier — remains empty-state / 0 actions (mid-risk/limited unlock is Phase 75)
- multi-step / sequential plan surfacing (Phase 74)
- new action generators, new action families, or model retraining
- threshold/gate policy redesign (Phase 72's gate logic is unchanged)
- ranking algorithm changes (winner selection for action #1 stays exactly as-is; only the *additional* slot is new)

Hard guardrail:
- `selected_invalid_winner_count`, `selected_surface_drift_count`, `operator_packet_contradiction_count` must remain `0` (`TRUST-01`-`TRUST-03`, carried from Phase 72).

</domain>

<decisions>
## Implementation Decisions

### 1) Top-k size
- **D-01:** Fixed `k=2`. Surface up to 2 actions for `full`-tier customers when ≥2 valid, distinct-action-family candidates exist in the selected plan's action set; otherwise surface 1 (unchanged from today). No dynamic/uncapped surfacing.

### 2) Selection rule
- **D-02:** Diversity-first, then rank. Action #1 = the current winner (unchanged ranking/selection logic — do not touch). Action #2 = the highest-ranked candidate from the selected plan whose `action_family` differs from action #1's family. If no second distinct-family candidate exists, surface only 1 action (no same-family duplicates, no padding).

### 3) Tier scope
- **D-03:** `full` tier only. `assisted_full` stays at exactly 1 action per Phase 72's locked allowlist/contract — do not modify Phase 72's `assisted_full` surfacing path.
- **D-04:** `limited` tier is untouched — remains 0 surfaced actions / empty-state. Out of scope for Phase 73 (belongs to Phase 75 if ever addressed).

### Claude's Discretion
- Where action-type distribution metrics are published: new artifact file vs. new columns/rows in an existing cohort evaluation artifact (e.g. `phase_60_cohort_eval_recourse_gate_table.csv` or `recourse_action_count_distribution.csv`) — pick whichever requires the least contract disruption while remaining additive.
- Whether institution-assisted (`action_type="institutional"`) candidates are eligible to fill action #2 for `full`-tier customers, vs. restricting action #2 to customer-only/behavioral/restructure/adjustment families — Phase 72 deferred institution-assisted inclusion for `assisted_full` specifically, but `full`-tier customers may already receive institution-assisted actions today as their primary winner, so Claude should determine the least-disruptive, most-defensible rule during planning/research and document it in the plan.
- Exact narrative/output shape for representing a second action (separate narrative block vs. extended single narrative) — must stay within `TRUST-04` (no claims beyond selected-plan evidence) and must not alter `selected_plan_id`/winner fields for action #1.
- Exact field/column naming for the second surfaced action and for action-type distribution metrics, as long as additive and documented in "Artifacts this phase produces".

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & requirements
- `.planning/ROADMAP.md` — Phase 73 section (goal, success criteria)
- `.planning/REQUIREMENTS.md` — `SURF-01`, `SURF-02`, `SURF-03`, `TRUST-04` definitions

### Prior phase context (directly relevant precedent)
- `.planning/phases/72-recoverability-gate-relaxation-controlled/72-CONTEXT.md` — locked `assisted_full` contract (exactly 1 action, customer-only allowlist) that Phase 73 must NOT modify
- `.planning/phases/72-recoverability-gate-relaxation-controlled/72-VERIFICATION.md` — confirms Phase 72 shipped trust-clean; Phase 73 must preserve this

No external specs/ADRs beyond the above — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `credit-coach/src/credit_coach/recourse/action_space.py` — defines `action_family` / `action_type` per action template (`LEGACY_ACTION_FAMILY_BY_ACTION_KEY`, `action_family()` property); this is the source of "distinct action family" classification for diversity-first selection.
- `credit-coach/src/credit_coach/recourse/generator.py` (~line 148, 293) — emits `action_family` per generated action; candidate actions for a selected plan should already carry this field.
- `credit-coach/src/credit_coach/cli/run_recourse.py` (~line 810, 1260-1340) — `primary_recommendation` / `_localized_projection_payload` is where the single surfaced action is currently projected into output; this is the natural seam for adding a second surfaced action.
- `credit-coach/src/credit_coach/evaluation/recoverability.py` (~line 173-201) — `recourse_mode` (`full` / `assisted_full` / `limited`) gating; Phase 73 must branch top-k logic on `recourse_mode == "full"` only.

### Established Patterns
- "Trust-clean" is a hard invariant carried from v2.5-v2.7: any surfaced change must preserve `selected_invalid_winner_count=0`, `selected_surface_drift_count=0`, `operator_packet_contradiction_count=0`.
- Additive artifacts over contract rewrites — Phase 72 added provenance fields rather than redefining canonical CSVs; Phase 73 should follow the same pattern for the second action and distribution metrics.
- Action #1 (the winner) selection/ranking logic is treated as a stable, unchanged seam across phases — Phase 73 must not alter it.

### Integration Points
- Action candidate set / family classification: `credit-coach/src/credit_coach/recourse/action_space.py`, `credit-coach/src/credit_coach/recourse/generator.py`
- Output projection (where action #2 gets surfaced): `credit-coach/src/credit_coach/cli/run_recourse.py`
- Recourse-mode gating (scope to `full` only): `credit-coach/src/credit_coach/evaluation/recoverability.py`
- Cohort evaluation / distribution metrics: `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py` and existing `recourse_action_count_distribution.csv` / `phase_60_cohort_eval_recourse_gate_table.csv` artifacts

</code_context>

<specifics>
## Specific Ideas

- Action #1 must remain byte-for-byte identical in selection/ranking to today's single-action output — Phase 73 is purely additive (an optional action #2 plus distribution metrics).
- "Distinct action family" is the diversity criterion — not distinct action key/template. Two different specific actions from the same family (e.g., two `behavioral` actions) do not both count toward the k=2 slots; action #2 must come from a different family than action #1.

</specifics>

<deferred>
## Deferred Ideas

- Raising `assisted_full`'s action cap above 1 — revisit only after Phase 73's `full`-tier top-k=2 is proven trust-clean (candidate for a future wave, not currently scheduled).
- `limited`-tier / mid-risk actionable surfacing — Phase 75 (Mid-Risk Segment Unlock).
- Multi-step / sequential plan surfacing — Phase 74 (Multi-Step Plan Surfacing).

</deferred>

---

*Phase: 73-action-surface-expansion*
*Context gathered: 2026-06-14*
