# Phase 35: Narrative Generation v2 - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Translate the hardened semantic, numeric, feasibility, execution, and offer contracts into clear, personalized, product-ready narratives. This phase hardens:
- narrative granularity
- personalization posture
- business vs technical split
- tone and persuasion policy

This phase does **not** reopen:
- action taxonomy or grouped semantic identity
- numeric target generation posture
- feasibility verdict logic
- difficulty and execution aggregation posture
- offer contract and rankability semantics
- broader product-surface rendering logic beyond the engine-owned narrative contract

</domain>

<decisions>
## Implementation Decisions

### Carry-Forward Decisions From Prior Phases
- Phase 18 remains authoritative for the engine-owned narrative skeleton:
  - canonical narrative lives inside engine output
  - one shared schema feeds buyer and analyst surfaces
  - `executive_summary`, `steps`, `checkpoints`, `reasons`, and `technical_reveal` remain the core structure
  - controlled vocabulary, template-driven wording, and deterministic output remain mandatory
- Phase 30 remains authoritative for semantic action identity:
  - `behavioral | structural | institutional`
  - canonical `action_family`
  - grouped action identity remains deterministic
- Phase 31 remains authoritative for numeric targets:
  - one canonical primary numeric target per action
  - current state, target, delta, unit, and due month remain engine-owned truth
- Phase 32 remains authoritative for feasibility truth:
  - business-safe feasibility outcome labels remain distinct from raw constraint trace
  - invalid or semantic-break actions remain outside default product-facing output
- Phase 33 remains authoritative for difficulty and execution truth:
  - difficulty and readiness remain separate from feasibility
  - default business output does not expose raw probabilities
- Phase 34 remains authoritative for offer truth:
  - `offer_contract` is nested and canonical
  - customer action remains primary story
  - offer remains an institution-side companion intervention

### Narrative Granularity
- Default reading order is locked as:
  - `executive_summary`
  - `steps`
  - `checkpoints`
  - `reasons`
- `action_summary` must stay semantically clean and readable.
- The primary numeric target should not crowd the first sentence of the step.
- The canonical placement for the primary numeric target is inside `expected_outcome`.
- Every default-visible step should show short business-safe execution realism cues:
  - feasibility outcome label
  - difficulty label
  - short follow-through note
- These cues should remain compact labels and short notes rather than dense sub-explanations.
- All three checkpoints remain visible in the narrative surface:
  - `4w` is dominant
  - `12w` and `24w` remain shorter supporting layers
- Checkpoint presence should stay explicit rather than collapsing later checkpoints behind hidden UI-only logic.

### Personalization Posture
- Narrative personalization should be anchored to:
  - current state
  - target state
  - timing
- Personalization should come from engine truth rather than from freeform persona writing.
- Segment posture may lightly shape tone or emphasis, but should not appear as explicit portfolio jargon in default copy.
- Default narrative should not say things like:
  - `high-risk recoverable segment`
  - `offer-needed segment`
- Behavior language should remain:
  - behavior-led
  - non-judgmental
- Narrative may describe disciplined payment behavior, lower utilization, or cleaner document posture, but must not moralize or shame.
- In offer-bearing plans:
  - the customer path remains the personalization anchor
  - institution support appears after and alongside that path
- Offer must never become the main narrative voice.

### Business vs Technical Split
- Default business output should carry only one primary numeric statement per step.
- Secondary metrics should remain in technical reveal rather than in the default story layer.
- Default business output should not expose raw probabilities.
- Instead it should expose:
  - readiness labels
  - difficulty labels
  - confidence labels
  - short risk wording
- Technical reveal must carry the minimum narrative-generation truth set:
  - `primary_numeric_target`
  - feasibility trace
  - difficulty drivers
  - `offer_contract`
  - `plan_execution_probability`
  - `approval_dependent_plan_probability`
  - `combined_plan_realization_probability`
- Default business-facing reasons should show only the top `2-3` principal reasons.
- These reasons should stay short and remediation-oriented.
- Full reason packs remain technical or proof-facing artifacts rather than default customer narrative payload.

### Tone And Persuasion Policy
- Default tone is locked as:
  - calm
  - confident
  - non-judgmental
- Narrative should be gently directive rather than purely descriptive or motivational.
- The product should be willing to say:
  - what to do
  - what matters first
  - what outcome is expected
- But it must not drift into sales copy, hype, or therapy-style coaching language.
- Negative-outcome wording should remain:
  - honest
  - non-threatening
- Valid examples include:
  - expected impact softens
  - readiness is delayed
  - early checkpoint weakens
- Fear language, pressure language, and internal model jargon should remain out of default product copy.
- Determinism remains first-class:
  - deterministic templates first
  - modest variation second
- Personalization should mainly come from numeric values, timing, checkpoint shape, feasibility state, difficulty state, and offer presence rather than from freeform expressive generation.

### Claude's Discretion
- Exact field additions within the existing narrative schema, as long as:
  - the business vs technical split stays explicit
  - prior canonical fields remain stable
- Exact localized sentence wording, as long as:
  - tone remains calm and non-judgmental
  - directives remain gentle
  - negative-outcome language remains honest but non-threatening
- Exact thresholding or ordering for top reasons, as long as:
  - only the top `2-3` appear in default narrative
  - the full reason pack remains recoverable in technical layers

</decisions>

<specifics>
## Specific Ideas

- The user wants Phase 35 to be the place where the engine can clearly say:
  - what this customer should do
  - what institutional support may be available
  - why the plan matters
  - how realistic the plan is
  - what happens over time
- The user explicitly does not want this phase to re-open already hardened numeric, feasibility, execution, or offer contracts.
- The user wants the default surface to feel personalized through:
  - current state
  - target
  - timing
  rather than through verbose or artificial persona-writing.
- The user wants each step to stay readable:
  - one main action meaning
  - one main numeric target
  - short realism signals
- The user wants all three checkpoints to remain visible, with `4w` carrying the strongest product emphasis.
- The user wants the tone to stay persuasive enough to guide action, but not so strong that it becomes hype, pressure, or marketing language.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [schema.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py)
  - already carries:
    - `RoadmapExecutiveSummary`
    - `RoadmapStepNarrative`
    - `OfferNarrative`
    - `RoadmapCheckpointNarrative`
    - `RoadmapReasonNarrative`
    - `RoadmapTechnicalReveal`
    - `CustomerRoadmapNarrative`
  - is the natural home for Phase 35 contract hardening
- [messaging.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/messaging.py)
  - already builds:
    - step narratives
    - offer narratives
    - executive summary
    - checkpoint narratives
    - reason narratives
    - technical reveal payloads
  - already formats:
    - primary numeric targets
    - difficulty labels
    - follow-through readiness
    - offer state wording
  - is the primary seam for Phase 35 implementation

### Established Patterns
- Narrative output is already engine-owned and deterministic.
- The existing system already prefers:
  - business-safe labels by default
  - technical completeness on reveal
- Phase 35 should extend this pattern rather than inventing a new rendering model.
- Offer-bearing steps already support a separate `offer_narrative`, which matches the user's requirement that offer remain companion-only.

### Integration Points
- Primary engine seams for Phase 35:
  - `credit-coach/src/credit_coach/data/schema.py`
  - `credit-coach/src/credit_coach/coaching/messaging.py`
  - `credit-coach/src/credit_coach/cli/run_recourse.py`
- Important downstream consumers to keep aligned:
  - runtime roadmap artifact generation
  - website and analyst typed mirrors in later surface phases
  - proof-facing and validation-facing consumers that rely on the same narrative contract

</code_context>
