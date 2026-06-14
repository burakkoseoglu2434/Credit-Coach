# Phase 66: Demo & Narrative Alignment - Context

**Gathered:** 2026-04-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 66 aligns demo surfaces and customer/operator narrative wording to the shipped `v2.5` system truth so recoverable vs structural-limited outcomes are obvious, deterministic, and audit-safe.

This phase owns:
- the **demo contract** (canonical sections + required/optional fields)
- the **narrative contract** (mode taxonomy + wording rules)
- mapping from shipped runtime truth (`recoverable_flag`, `recourse_mode`, `recommendation_mode`, signal + reason codes) into customer/operator readable explanations
- drift-prevention rules across demo, packet, explanation pack, and reports

This phase does not own:
- planner redesign, threshold redesign, or new action types
- any “uplift” / causal framing changes to evaluation logic (only wording and what is shown)
- changes to trust baseline: winner integrity, DICE contender quality, selected-surface consistency, operator packet coherence

</domain>

<decisions>
## Implementation Decisions

### 1) Canonical demo contract (one-screen story)

Define a **single canonical customer demo screen** (“Decision → Mode → Why → Path → Expected outcome”) with fixed sections that always appear in the same order.

**Always-visible sections (in order):**
1. **Decision & posture**
   - decision outcome (`APPROVED|CONDITIONAL|REJECTED`)
   - `recourse_mode` (`full|limited`) and **narrative posture** (`actionable|informational`)
   - readiness (`expected_readiness`, `time_to_readiness`) as the timeline anchor
2. **Recoverability call**
   - “Recoverable now?” derived from shipped `recoverable_flag`
   - one-line “why” derived from shipped reason families (not freeform)
3. **What we will (and will not) recommend**
   - if actionable: show selected path summary + next steps
   - if informational: show explicit “no selected plan promoted” + the gating reason family
4. **Selected path / route (only when actionable)**
   - selected path type (`customer_only|hybrid|institution_assisted`)
   - selected path one-sentence customer summary (engine-owned render)
   - 3-step “first actions” list (engine-owned step narratives)
5. **Realistic outcome framing**
   - movement potential shown as **descriptive forecast**, not a promise
   - explicit disclaimer: “not a guarantee; depends on execution and institution decisions”
6. **Proof rail (small)**
   - show *concentration* and *honesty* signals, not approval uplift (see Metrics rules)

**Demo must include two canonical customer cases:**
- **Case A (recoverable/full/actionable)**: denied today but actionable
- **Case B (non-recoverable/limited/informational)**: denied today and structural-limited or not currently actionable

Rationale: the product truth is the separation; the demo must show both modes to be honest.

### 2) Narrative taxonomy (minimal modes)

Lock a 2-level taxonomy so we can satisfy `NARR-01..03` without inventing a third runtime mode:

- `narrative_type` (required, customer + demo visible):
  - `actionable` when `recommendation_mode == "actionable"` (i.e., `recourse_mode == "full"`)
  - `informational` when `recommendation_mode == "informational"` (i.e., `recourse_mode == "limited"`)

- `informational_subtype` (required when informational; customer visible as a short label + 1 supporting sentence):
  - `structural_limited` when `recoverability_bucket == "structural_limited"` OR any hard structural blocker present
  - `not_currently_actionable` when soft blocker families dominate (time / offer / low impact) or `mid_risk` fails recoverable band

Locked decision:
- `mid_risk` remains `not_currently_actionable` (do not collapse into `structural_limited` messaging).

Rule: **never** present a customer as “actionable” if `recourse_mode == "limited"`; the gate is the truth.

### 3) Customer-facing wording rules (deterministic, safe)

Customer text must be rendered from engine-owned truth + stable templates.

**Tone rules:**
- “Honesty beats hype”: do not imply approval guarantee, business uplift, or inevitability.
- Use “can / may / could” only when paired with the gating conditions (execution, time, institution).
- Prefer “decision threshold” / “approval readiness” over internal model jargon.
- Avoid vague platitudes (“improve profile”, “make progress”) — follow Phase 59 suppression rules.

**Required customer phrases (semantic templates, not freeform prose):**
- Rejected but recoverable (actionable):
  - “Not approved today. A governed path exists that can move you closer to the decision threshold **if** the steps are completed.”
- Not currently recoverable (informational → not_currently_actionable):
  - “We cannot recommend a safe action plan **right now** because a key condition is missing (time window, offer eligibility, or impact).”
- Structural-limited (informational → structural_limited):
  - “With the current risk distance and available evidence, there is no credible action path to reach the threshold in a governed way.”
- Institution-assisted path:
  - “This route depends on institution approval/terms. We only proceed if the institution confirms eligibility.”
- Hybrid path:
  - “This route combines customer steps with institution support; both are required for the route to land.”

**Mapping rule for “why” (customer):**
- Show max 2–3 bullets derived from reason-code families, in this order:
  1) distance-to-threshold framing (near / mid / structural-limited)
  2) path evidence (rankable path exists / none)
  3) blocker family (time / offer / low impact) *only if it’s decisive*

### 4) Operator-facing wording rules (extra detail, no drift)

Operators see everything customers see **plus** the auditable internals needed to defend the posture without leaking debug dumps.

**Operator-only additions (short view or appendix):**
- `approval_gap`, `recoverability_bucket`, `threshold_reach_possible`
- `recoverable_reason_codes`, `recoverability_signal_reason_codes`, `recourse_gate_reason_codes`
- hard vs soft blocker lists (explicit)
- selected path movement fields when actionable:
  - `movement_score`, `threshold_reach_probability`, `threshold_reach_priority_flag`, `movement_rank_reason_codes`
- contract/version fields:
  - `recoverability_classifier_version`, `recourse_gate_version`, `selected_path_render_version`, `selected_recommendation_projection_version`

**Framing rule (operator):**
- `recourse_mode` is the enforced posture; any “interesting but suppressed” signals remain subordinate evidence.
- When limited mode is triggered, operators must see a single “limited-mode rationale” label derived deterministically from the same reason families used in customer copy.

### 5) Demo proof / metrics display rules (no uplift language)

**Customer screen (allowed):**
- posture: `narrative_type`, `recourse_mode`
- movement potential: `selected_path_movement_strength` + `threshold_reach_probability` (actionable only)
- distance framing: `approval_gap` (optionally rounded), and/or “near/mid/high distance” label
- readiness timeline: `expected_readiness` and checkpoint week(s)
- execution realism (actionable only): `plan_execution_probability` as “follow-through strength (estimated)”

**Portfolio proof rail (allowed, descriptive):**
- Primary: distance posture as a **band label** (`near_threshold|mid_risk|structural_limited`)
- Secondary: numeric distance as `approval_gap` (rounded; never the headline)
- `recoverable_customer_rate`
- `recommendation_mode_distribution` (actionable vs informational share)
- concentration metrics from Phase 65 outputs (e.g., movement rate / strong movement rate) **phrased as descriptive model evidence**

**Must stay internal (not in customer/demo default):**
- raw gate traces, `NEEDS_REVIEW`, candidate policy comparison tables, SHAP contribution dumps
- fairness penalty / internal planner diagnostics beyond the bounded “technical reveal” view

**Language constraints:**
- no “lift”, “uplift”, “increases approvals”, or causal phrasing
- prefer: “concentrates movement potential”, “descriptive evidence”, “observed vs predicted (descriptive)”

### 6) Surface alignment and drift prevention

**Source-of-truth rule:** the Python engine emits the narrative posture and copy; website/demo surfaces render it without re-authoring.

Surfaces that must match exactly (same underlying fields, same posture):
- selected recommendation text (selected projection)
- selected path customer summary + operator summary
- recoverability explanation family (recoverable vs not + why)
- limited-mode explanation (explicit “no plan promoted” posture)

Drift prevention mechanisms:
- add a `narrative_contract_version` constant emitted with the customer roadmap summary and operator/explanation artifacts
- render all customer-facing “posture” and “why” text from a single engine-owned helper (no website-side inference)
- website demo schema must carry and display `recourse_mode`, `recommendation_mode`, `narrative_type`, and `informational_subtype` (or equivalent) directly from artifacts

Locked decision (website demo):
- Website/demo must display **only engine-owned fields** for posture + narrative + step details (no frontend inference/mapping). If a field is absent, the UI shows an explicit “Unavailable in this view” placeholder rather than synthesizing content.

### Claude's Discretion
- Exact UI layout (cards vs stacked sections) as long as the section order and required fields stay intact.
- Exact TR/EN phrasing inside the locked templates, as long as semantics and disclaimers remain deterministic and safe.
- Whether `informational_subtype` is encoded as a dedicated field or derived from reason codes at render time, as long as the mapping remains stable and testable.

</decisions>

<specifics>
## Specific Ideas

- Treat Phase 66 as a **copy contract** problem: “what must always be true, in what order, with what safe language,” not a design refresh.
- Make “recoverable vs limited” visually and linguistically unavoidable: a top-level posture badge + explicit “selected plan promoted” yes/no.
- Use Phase 59 render suppression rules to prevent generic copy from becoming the demo story.
- For informational/limited mode: explicitly answer “what would have to change before we can recommend actions” (time window, offer eligibility, impact evidence), without inventing new actions.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `credit-coach/src/credit_coach/evaluation/recoverability.py`: canonical recoverability signal, classifier, and gate truth (`recoverable_flag`, `recourse_mode`, `recommendation_mode`, reason codes).
- `credit-coach/src/credit_coach/cli/run_recourse.py`: applies gate to roadmap and currently clears narrative steps in limited mode; Phase 66 should align the remaining narrative/executive summary with limited-mode posture.
- `credit-coach/src/credit_coach/coaching/messaging.py`: produces `CustomerRoadmapNarrative` and executive summary cards; best place to centralize deterministic customer-facing templates by `narrative_type`.
- `credit-coach/src/credit_coach/ops/operator_review.py` + `credit-coach/src/credit_coach/data/schema.py`: operator packet surfaces; should consume the same mode + reason families and display operator-only detail without leaking debug dumps.
- `credit-coach-website/server/services/live-demo.ts`: currently infers step details/probabilities; Phase 66 must remove that inference for demo surfaces and show engine-owned posture/copy to prevent drift.
- `credit-coach-website/shared/demo-schema.ts`: schema contract for demo; will need to carry v2.5 posture fields explicitly (mode + recoverability) to keep the UI deterministic.

### Established Patterns
- “Engine is truth owner; website is typed consumer” (reinforced in `.planning/PROJECT.md` and `credit-coach-website/CURATED_DEMO_HANDOFF.md`).
- Selected-surface projection is authoritative; empty-state is trust-safe and reused for limited mode (Phase 47/63 posture).

### Integration Points
- Customer artifacts: `customer_roadmap.json` (`summary` + `narrative`) must carry posture fields + narrative contract version.
- Operator artifacts: operator packet and explanation pack must show consistent posture and a bounded “why limited” rationale.
- Website demo: must consume the same fields and must not recompute “who is recoverable” or “why” in frontend code.

</code_context>

<deferred>
## Deferred Ideas

- Any new runtime mode beyond `full|limited` (explicitly deferred by Phase 63).
- Any “coaching for structural-limited” that introduces new action types or new data sources.
- Any causal language or uplift claims; those require separate evidence and phase scope.

</deferred>

---

*Phase: 66-demo-narrative-alignment*
*Context gathered: 2026-04-10*
