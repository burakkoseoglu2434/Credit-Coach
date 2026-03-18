# Phase 18: Decision Narrative & Product Output Translation - Context

**Gathered:** 2026-03-18
**Status:** Ready for replanning

<domain>
## Phase Boundary

Translate engine-native recommendation output into deterministic, buyer-friendly and analyst-friendly product narratives without weakening truth, governance, or traceability. This phase builds a controlled translation layer with executive summaries by default and expandable technical detail on demand. It does not reopen planning logic, behavior-aware ranking, trajectories, offer optimization, learning-loop math, or portfolio proof from earlier phases; it converts those locked truths into one canonical business-first output contract.

</domain>

<decisions>
## Implementation Decisions

### Carry-Forward Decisions From Phases 12-17
- Phase 12 typed-action semantics remain authoritative:
  - action outputs must resolve to meaningful behavioral, structural, or institutional actions
  - raw feature deltas must not become the default product-facing language
- Phase 13 behavior-aware probabilities remain authoritative:
  - execution-aware and partial-execution logic stay engine-side
  - narrative should describe them, not reinterpret them
- Phase 14 trajectory structure remains authoritative:
  - canonical `phases[]`
  - canonical `checkpoints[]`
  - `4w > 12w > 24w`
- Phase 15 offer contract remains authoritative:
  - offer state is explicit and machine-readable
  - offer logic is not redefined by website copy
- Phase 16 learning-loop and confidence-adjacent evidence remain authoritative:
  - narrative may summarize confidence
  - it must not fabricate confidence
- Phase 17 portfolio proof remains authoritative:
  - product-readiness, reality-gap, and demo-fit evidence are inherited truth inputs
- Engine-side artifacts remain the single source of truth
- Website and analyst surfaces are renderers, not alternate interpreters

### Canonical Narrative Object Shape
- Canonical narrative must live inside engine output, not in website-only formatter logic
- The correct model is:
  - engine produces truth and translated truth
  - UI consumes and renders
- Narrative must be canonical at three levels:
  - plan-level `executive_summary`
  - step-level action narrative
  - checkpoint-level narrative
- Raw truth and translated truth must live in the same artifact, but as separate layers
- Recommended structure is:
  - `customer_roadmap.phases`
  - `customer_roadmap.checkpoints`
  - `customer_roadmap.narrative`
- Minimum plan-level `executive_summary` fields are:
  - `risk_start`
  - `recommended_path`
  - `offer_status`
  - `checkpoint_4w_summary`
  - `expected_result`
  - `narrative_confidence`
  - `decision_view`
  - `time_to_readiness`

### Step, Checkpoint, Offer, And Reason Narration
- Minimum step-level narrative fields are:
  - `action_summary`
  - `why_this_matters`
  - `expected_outcome`
  - `what_happens_if_done`
  - `what_happens_if_not_done`
- Strongly preferred optional step field:
  - `action_timing_hint`
- Minimum checkpoint-level narrative fields are:
  - `expected_state`
  - `success_condition`
  - `failure_implication`
- Strongly preferred optional checkpoint field:
  - `review_action`
- Offer narration must live as a separate sub-block rather than being mixed into ordinary action narrative
- Minimum offer narrative fields are:
  - `offer_explanation`
  - `why_offered`
  - `if_accepted`
  - `if_not_accepted`
- Strongly preferred optional offer field:
  - `offer_terms_summary`
- Raw adverse-action reason codes must not appear in default UI
- Canonical reason translation should expose, per principal reason:
  - `reason_title`
  - `reason_description`
  - `remediation_hint`
- Strongly preferred optional reason field:
  - `reason_severity`

### Controlled Technical Reveal And Consistency
- Technical detail must not be deleted; it must move into a controlled reveal layer
- Controlled technical reveal must live under the narrative branch, not as a separate artifact
- Recommended structure is:
  - `customer_roadmap.narrative.technical_reveal`
- Minimum technical reveal fields are:
  - `feature_changes`
  - `explainability_reasons`
  - `constraints_applied`
  - `approval_dependencies`
  - `diagnostic_flags`
- Strongly preferred optional reveal field:
  - `confidence_inputs`
- Narrative confidence labels must be:
  - `high`
  - `moderate`
  - `low`
- Raw confidence scores may remain engine-side in machine-readable form, but default UI should show only the label
- If the raw score is serialized, it should live in technical reveal rather than executive summary
- Narrative consistency policy must be strict:
  - template-driven
  - controlled vocabulary
  - deterministic fills
- Phase 18 must not introduce freeform generative copy as the canonical production surface

### UI-Ready Schema Boundary
- The canonical UI-ready schema source must be engine-side narrative schema
- Website schema must not become source-of-truth
- Website may keep a typed mirror, but only as a consumer contract
- There must be one shared canonical schema for:
  - website surfaces
  - analyst surfaces
- Website and analyst views may differ only in rendering and visibility, not in underlying truth
- Analyst surfaces may expose more of the same data, especially:
  - full narrative
  - full `technical_reveal`
  - confidence details
  - diagnostic flags
- Acceptance for Phase 18 requires all of the following:
  - the same customer artifact can render both website and analyst views
  - default view remains business-first
  - technical reveal remains present and intact
  - TR and EN output remain template-consistent
  - UI does not need to perform critical translation or inference
  - narrative output is deterministic for the same input

### Claude's Discretion
- Exact JSON nesting under `customer_roadmap.narrative` as long as:
  - executive summary
  - step-level narrative
  - checkpoint-level narrative
  - technical reveal
  remain explicit and machine-readable
- Exact threshold mapping from raw confidence to:
  - `high`
  - `moderate`
  - `low`
- Exact sentence wording for action, checkpoint, offer, and reason templates as long as vocabulary remains controlled and deterministic
- Exact TR/EN token choices as long as the same semantic contract is preserved across languages

</decisions>

<specifics>
## Specific Ideas

- The user explicitly wants Phase 18 to become the phase where engine output turns into “what should this customer do and why?” rather than a feature-delta dump.
- The user wants a controlled translation layer:
  - not a lossy marketing simplification
  - not a raw engine trace
- The user wants the default view to answer quickly:
  - what is the customer situation
  - what path is recommended
  - whether an offer exists
  - what happens by week 4
  - when readiness is expected
- The user wants technical detail preserved, but behind controlled reveal patterns rather than in the default UI.
- The user wants website and analyst experiences to differ only in how much of the same artifact they show.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `credit-coach/src/credit_coach/data/schema.py`
  - already carries typed `PlanAction`, `TrajectoryPhase`, and `TrajectoryCheckpoint`
  - is the natural home for canonical narrative-bearing output contracts
- `credit-coach/src/credit_coach/coaching/messaging.py`
  - already contains adverse-action reason normalization and human-readable reason templates
  - is the natural seam for principal-reason translation
- `credit-coach/src/credit_coach/cli/run_recourse.py`
  - already serializes customer roadmap artifacts
  - is the natural seam for emitting a narrative layer alongside raw plan truth
- `credit-coach-website/shared/demo-schema.ts`
  - already defines a consumer schema for single-customer demo output
  - should evolve into a typed mirror of engine-side narrative output, not a competing source contract
- `credit-coach-website/client/src/lib/demo-formatters.ts`
  - already performs significant presentation translation
  - is evidence that translation logic should move upstream into engine-owned schema where possible
- `credit-coach-website/client/src/pages/DemoCenterPage.tsx`
  - already has an executive-summary style surface and controlled reveal patterns
  - is a good downstream consumer for the new narrative contract
- `credit-coach-website/server/services/live-demo.ts`
  - currently bridges raw engine output into website-ready story text
  - should become thinner as Phase 18 moves canonical translation into engine output

### Established Patterns
- Machine-readable artifact truth comes first; UI and markdown are derived views
- Earlier phases already locked:
  - typed actions
  - behavior-aware execution
  - trajectory checkpoints
  - offer state
  - confidence and evidence seams
- Default buyer-facing UI should not leak raw internal jargon
- Controlled reveal is already an accepted UI pattern in the website

### Integration Points
- Phase 18 should primarily hook into:
  - `credit-coach/src/credit_coach/data/schema.py`
  - `credit-coach/src/credit_coach/coaching/messaging.py`
  - `credit-coach/src/credit_coach/cli/run_recourse.py`
  - possibly narrative helpers under coaching, recourse, or presentation seams
- Downstream consumers should include:
  - `credit-coach-website/shared/demo-schema.ts`
  - `credit-coach-website/server/services/live-demo.ts`
  - `credit-coach-website/client/src/lib/demo-formatters.ts`
  - `credit-coach-website/client/src/pages/DemoCenterPage.tsx`
- Regression coverage should likely extend through both:
  - engine-side schema or serialization tests
  - website-side consumer contract tests

</code_context>

<deferred>
## Deferred Ideas

- Large-scale website repositioning and Demo Center information architecture remain later website phases
- Curated demo sync pipelines and proof snapshot versioning remain Phase 19 work
- Investor and proof narrative surfaces remain later productization phases
- Any freeform LLM-driven copy generation layer is out of scope for Phase 18

</deferred>

---
*Phase: 18-decision-narrative-product-output-translation*
*Context gathered: 2026-03-18*
