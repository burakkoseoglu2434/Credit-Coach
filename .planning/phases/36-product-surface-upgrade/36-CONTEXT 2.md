# Phase 36: Product Surface Upgrade - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Render the hardened semantic, numeric, feasibility, execution, offer, and narrative contracts into a clearer, product-ready UI surface. This phase hardens:
- surface hierarchy
- action card contract
- offer surfacing
- business vs technical UI boundary

This phase does **not** reopen:
- action taxonomy or grouped semantic identity
- numeric target generation posture or contract
- feasibility verdict semantics
- difficulty and execution aggregation posture
- offer contract and rankability semantics
- core narrative generation logic beyond product-surface rendering
- broader website redesign beyond the scoped demo and product-surface upgrade

</domain>

<decisions>
## Implementation Decisions

### Carry-Forward Decisions From Prior Phases
- Phase 30 remains authoritative for semantic action identity:
  - `behavioral | structural | institutional`
  - canonical `action_family`
  - deterministic grouped actions
  - explicit `business_view` vs `technical_view`
- Phase 31 remains authoritative for numeric targets:
  - one canonical primary numeric target per action
  - current state, target, delta, unit, and due month remain engine-owned truth
- Phase 32 remains authoritative for feasibility truth:
  - `valid | clipped | repaired | provisional | invalid`
  - business defaults show only outcome-safe feasibility labels
  - raw constraint traces remain technical-only
- Phase 33 remains authoritative for execution truth:
  - business defaults show difficulty and readiness wording rather than raw probabilities
  - technical layers retain full difficulty and probability traces
- Phase 34 remains authoritative for offer truth:
  - `offer_contract` is nested and canonical
  - customer action remains the primary story
  - offer remains an optional institution-side companion
- Phase 35 remains authoritative for narrative structure:
  - `executive_summary -> steps -> checkpoints -> reasons`
  - one primary numeric statement per step in `expected_outcome`
  - calm, confident, gently directive, non-judgmental tone
  - technical reveal remains a separate, explicit layer

### Surface Hierarchy
- Default single-customer surface order is locked as:
  - `executive_summary`
  - `action cards`
  - `checkpoint strip`
  - `offer panel`
  - `reasons`
  - `technical reveal`
- The surface should be action-first rather than phase-first.
- Phase structure should still be visible, but only as lightweight organization.
- The primary user question on first read is:
  - what should I do
  - by when
  - how realistic is it
- Checkpoint truth should sit immediately above the action list as a compact strip.
- The checkpoint strip must always show:
  - `4w`
  - `12w`
  - `24w`
- `4w` should remain visually dominant.
- Reasons should sit after the main action flow and before technical reveal.
- Reasons should explain why the plan exists without interrupting the action-first reading path.

### Action Card Contract
- The action card remains the main product unit of meaning.
- The card headline should be the action, not the phase.
- Phase should appear only as a lightweight badge or grouping signal.
- Default action card minimum content is locked as:
  - `action_summary`
  - `expected_outcome`
  - `action_timing_hint`
  - short feasibility label
  - short difficulty label
  - short follow-through note
- Each action card should close the core business questions in one glance:
  - what to do
  - what happens
  - by when
  - how realistic it is
- Default card content should expose only one primary numeric statement.
- That numeric statement should remain inside `expected_outcome`.
- Secondary metrics should not be promoted into the default card body.
- Action cards should support a business-safe expanded state.
- Expanded state may show:
  - `why_this_matters`
  - `what_happens_if_done`
  - `what_happens_if_not_done`
- Expanded state should remain explanatory rather than technical.
- The expansion is the last business explanation layer before technical reveal.

### Offer Surfacing
- Offer panels should appear only for offer-bearing plans.
- The canonical product model remains:
  - customer action plus optional offer companion
- Offer should therefore surface in two layers:
  - a short companion signal inside the relevant action card
  - a fuller dedicated offer panel later in the surface
- Default offer panel minimum content is locked as:
  - `offer_explanation`
  - `why_offered`
  - `offer_terms_summary`
  - product-safe state label
- State wording should preserve the distinction between:
  - institution approval dependency
  - customer acceptance dependency
- Conditional or not-yet-active offers should remain visible on default surfaces.
- But they must be described honestly as:
  - conditional
  - not yet active
- Offer should never become the dominant story on the page.
- The customer path remains primary, with institution support layered behind it.

### Business vs Technical UI Boundary
- UI-side narrative fallback is explicitly disallowed.
- If engine-owned narrative or surface fields are missing, the UI must not invent substitute meaning.
- Allowed frontend transforms are limited to presentation-level behavior:
  - locale selection
  - formatting
  - ordering
  - empty-state rendering
- UI must not add semantic inference, synthetic guidance, or phase-specific fallback copy.
- Technical reveal should live at the end of the page as a collapsed analyst-style section.
- Business flow should therefore remain clean by default while preserving access to the underlying truth.
- If schema drift or missing fields occur, UI should:
  - fail soft
  - hide the broken subsection
  - show a neutral unavailable state when needed
- UI should never invent substitute recommendations, reasons, or outcomes to paper over missing engine fields.

### Claude's Discretion
- Exact visual grouping and component composition as long as:
  - action-first hierarchy remains intact
  - phase grouping stays lightweight
  - checkpoint strip remains above the action list
- Exact empty-state wording as long as it remains neutral and does not introduce new semantic meaning
- Exact offer-panel layout as long as:
  - short companion signal stays near the action card
  - detailed offer narrative stays in the dedicated offer section
- Exact collapse treatment for technical reveal as long as it remains:
  - default closed
  - end-of-page
  - sourced entirely from engine-owned truth

</decisions>

<specifics>
## Specific Ideas

- The user wants Phase 36 to make the website feel more actionable without letting the website become a second interpretation engine.
- The desired first-read journey is:
  - understand the situation
  - understand the next actions
  - understand the checkpoint horizon
  - understand institutional support
  - understand why this plan exists
- The user wants action cards to become the main product object, not phase cards.
- Phase should remain visible only as a light organizational cue.
- The user wants each visible action card to answer:
  - what to do
  - what numeric result is targeted
  - when it matters
  - how realistic it is
- Offer visibility should be explicit but secondary.
- The user explicitly does not want placeholder or local UI-generated narratives to fill gaps if the engine contract is missing or incomplete.
- The user wants technical detail to remain available, but only at the end of the page and only on demand.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [DemoCenterPage.tsx](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/client/src/pages/DemoCenterPage.tsx)
  - already serves as the primary single-customer product surface
  - already consumes `executive_summary`, checkpoints, phases, reasons, and technical reveal
  - currently still makes some local display decisions such as offer presence and section composition
  - is the main seam for applying the new action-first hierarchy
- [RoadmapPhaseCard.tsx](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/client/src/components/RoadmapPhaseCard.tsx)
  - currently remains phase-led
  - currently includes fallback narrative helpers such as:
    - `phaseNarrative(...)`
    - `fallbackExpectedOutcome(...)`
    - `fallbackTimingHint(...)`
  - is the main drift risk because it can invent copy outside the engine contract
  - should likely be reshaped or replaced by a stricter action-card renderer in this phase
- [demo-schema.ts](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/shared/demo-schema.ts)
  - already provides the typed mirror for single-customer roadmap artifacts
  - is the correct seam for tightening UI contract consumption rather than adding ad hoc page-local types
- [demo-formatters.ts](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/client/src/lib/demo-formatters.ts)
  - remains a valid presentation-only seam for formatting and locale-safe rendering
  - should not become a semantic inference layer

### Established Patterns
- Prior phases already established that:
  - engine artifacts are the source of truth
  - business-first read comes before technical detail
  - technical reveal stays available but collapsed
- Phase 22 and later website work already moved toward:
  - executive-first reading
  - reduced metric clutter
  - technical detail on demand
- Phase 36 should extend that direction while removing remaining UI-side narrative invention.

### Integration Points
- Primary implementation surfaces for Phase 36:
  - `credit-coach-website/client/src/pages/DemoCenterPage.tsx`
  - `credit-coach-website/client/src/components/RoadmapPhaseCard.tsx`
  - `credit-coach-website/shared/demo-schema.ts`
- Supporting presentation seams:
  - `credit-coach-website/client/src/lib/demo-formatters.ts`
  - shared page and section components already used by the Demo Center
- Important downstream constraint:
  - the website must remain a typed consumer of engine-owned artifacts rather than a second narrative generator

</code_context>

<deferred>
## Deferred Ideas

- Any broader website-wide redesign beyond the scoped demo and product-surface upgrade remains outside this phase.
- Any new engine-side narrative semantics beyond the already locked contracts from Phases 30-35 remain outside this phase.

</deferred>

---
*Phase: 36-product-surface-upgrade*
*Context gathered: 2026-03-22*
