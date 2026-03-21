# Phase 34: Offer Layer Integration - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Make institution-side actions explicit through a separate offer layer with typed terms, approval and acceptance semantics, and product-safe visibility rules. This phase hardens:
- canonical offer contract shape
- offer vs customer-action coexistence
- approval, acceptance, and rankability semantics
- business vs technical visibility of offer truth

This phase does **not** reopen:
- action taxonomy or grouped semantic identity
- numeric target generation posture
- feasibility verdict semantics
- difficulty and execution modeling posture
- broader narrative-generation v2 beyond offer-specific wording
- full product surface redesign

</domain>

<decisions>
## Implementation Decisions

### Carry-Forward Decisions From Prior Phases
- Phase 30 remains authoritative for semantic action identity:
  - `behavioral | structural | institutional` stays final
  - `action_family` remains canonical
  - grouped semantic identity remains deterministic
  - `business_view` vs `technical_view` remains engine-owned
- Phase 31 remains authoritative for customer-specific numeric targets:
  - one canonical primary numeric target per action
  - business-friendly metric identity
  - feasibility-neutral generation posture
- Phase 32 remains authoritative for feasibility truth:
  - `valid | clipped | repaired | provisional | invalid`
  - `repair-if-safe, reject-if-semantic-break`
  - `provisional` already means dependency-gated realism rather than raw invalidity
- Phase 33 remains authoritative for follow-through truth:
  - difficulty and execution remain separate from feasibility
  - approval-dependent execution probability already exists and must stay distinct

### Canonical Offer Contract Shape
- `PlanAction` should remain the canonical institutional action carrier.
- But offer truth should no longer live as a loose set of flat fields alone.
- Phase 34 should harden an explicit nested offer contract under the action, for example:
  - `offer_contract`
- The institutional action remains the semantic owner.
- The offer contract remains the explicit institution-side commercial or policy payload attached to that action.
- Minimum canonical offer contract fields are locked:
  - `offer_type`
  - `offer_family`
  - `offer_terms`
  - `offer_terms_complete`
  - `requires_acceptance`
  - `requires_institutional_approval`
  - `institutional_approval_state`
  - `offer_policy_arm`
  - `offer_scoring_profile`
  - `term_generation_rule`
- `offer_terms` should be semi-typed:
  - known canonical fields stay stable and typed
  - a small extension map is allowed for specialized term families
- Locked canonical known term fields:
  - `payment_delta_monthly`
  - `discount_amount`
  - `discount_pct`
  - `term_extension_months`
  - `interest_rate_delta`
  - `grace_period_weeks`
- Source-of-truth offer identity should stay action-level.
- Plan-level offer truth should be derived from action-level offer contracts rather than authored separately.

### Offer vs Customer-Action Coexistence
- The canonical model should be:
  - customer action plus optional offer companion
- An offer is not its own detached plan object.
- It remains the institution-side intervention that can accompany a customer action path.
- A semantic step may carry both:
  - the customer-facing action narrative
  - an attached offer narrative
- But the offer must remain a separate sub-block rather than collapsing into the same action sentence.
- The main action summary should not blend customer action and institution offer into one ambiguous sentence.
- Canonical plan posture:
  - one active offer branch at a time
- Multiple institutional possibilities may exist during generation, but a final canonical plan should carry only one active offer path.
- In product story hierarchy:
  - customer action remains the main story
  - offer remains the supporting institutional intervention
- This prevents offer-bearing plans from turning into raw commercial dumps instead of customer recovery paths.

### Approval, Acceptance, And Rankability Semantics
- Locked state distinction:
  - `approval pending` means a supply-side gate: the institution has not yet activated the offer as a live intervention
  - `acceptance pending` means a customer-side realization gate: the offer is live and complete, but the customer has not yet accepted it
- Minimum rankable offer contract is locked as:
  - `offer_terms_complete = true`
  - `institutional_approval_state in {approved, not_required}`
  - one active offer branch
  - non-placeholder semantic offer
- Offer acceptance is **not** a blocker for contender eligibility.
- Therefore:
  - an offer that still requires customer acceptance can still become the winning plan
- Acceptance truth should instead remain part of realization and expected-value modeling rather than rankability filtering.
- An offer-bearing plan should be treated as `provisional` when:
  - approval is `pending` or `unknown`
  - terms are materially incomplete
  - an institution-side external dependency means the offer branch is not yet executable
- A plan should **not** become provisional merely because the customer still needs to accept the offer.

### Business vs Technical Visibility Of Offer Truth
- Business-facing default offer output should show:
  - `offer_explanation`
  - `why_offered`
  - `offer_terms_summary` when available
  - approval or acceptance state expressed in product language
- Locked product-language distinction:
  - approval pending -> `kurum onayina bagli`
  - acceptance pending -> `musteri kabulune bagli`
- Default business surfaces should not expose raw offer scoring or policy metadata.
- Minimum technical reveal set is locked as:
  - full `offer_contract`
  - `offer_acceptance_probability`
  - `approval_dependent_probability`
  - `offer_policy_arm`
  - `offer_scoring_profile`
  - `term_generation_rule`
- Non-rankable or incomplete offers should still appear on default product surfaces only when they can be honestly expressed as:
  - conditional
  - not yet active
- Fully non-executable placeholders should not appear on default customer-facing surfaces.
- Those should remain technical-review-only artifacts.

### Claude's Discretion
- Exact field names for the nested offer contract as long as:
  - action-level source-of-truth remains intact
  - plan-level offer summaries remain derived
- Exact extension mechanism for typed-plus-flexible offer terms as long as:
  - canonical fields remain stable
  - specialized terms do not leak into ad hoc untyped chaos
- Exact wording for product-facing offer states as long as the distinction remains explicit between:
  - institution approval dependency
  - customer acceptance dependency
- Exact serialization strategy for bridging legacy flat fields into the new nested contract as long as downstream runtime, proof, and product consumers remain deterministic.

</decisions>

<specifics>
## Specific Ideas

- The user wants Phase 34 to stop treating institution-side actions as semi-hidden metadata attached to a step.
- Instead, institutional interventions should become explicit offer objects that still stay anchored to the semantic action layer.
- The user explicitly does **not** want offer semantics to displace the customer story.
- The canonical product posture should therefore read as:
  - what the customer should do
  - what institutional support is available alongside it
- Rankability should depend on institutional readiness and term completeness, but not on whether the customer has already accepted the offer.
- Product surfaces should express incomplete offers honestly:
  - conditional
  - not yet active
  - pending approval
- But placeholder institution-side artifacts should stay out of the default customer-facing view.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [action_space.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/action_space.py)
  - already defines institutional action templates
  - already carries offer-facing metadata such as:
    - `offer_type`
    - `requires_acceptance`
    - `offer_family`
    - `offer_scoring_profile`
    - `term_generation_rule`
    - `offer_policy_arm`
  - is the natural seed source for canonical offer identity
- [offer_optimization.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/offer_optimization.py)
  - already builds structured offer terms through `build_offer_contract(...)`
  - already distinguishes rankable offer actions from incomplete or approval-gated ones
  - already estimates:
    - offer acceptance probability
    - offer proxy deltas
  - is the natural seam for hardening approval, acceptance, and rankability semantics
- [schema.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py)
  - already carries flat offer-related fields on `PlanAction`
  - already has an `OfferNarrative` contract for product-facing offer wording
  - is the correct seam to introduce a nested canonical offer contract while preserving product and technical views
- [messaging.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/messaging.py)
  - already supports separate `offer_narrative` blocks under step narratives
  - is the right seam for keeping customer action wording primary while attaching institution-side offer explanations separately
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py)
  - already serializes both action-level and plan-level offer metadata into runtime artifacts
  - will need to bridge legacy flat fields toward the hardened nested offer contract without pushing interpretation to downstream consumers

### Established Patterns
- Prior phases already established a strong rule:
  - canonical truth should be engine-owned
  - product surfaces should consume rather than reinterpret it
- Phase 32 established the visibility split pattern:
  - business default shows outcome-safe wording
  - technical layers keep raw trace and diagnostics
- Phase 33 preserved that pattern for difficulty and execution truth.
- Phase 34 should mirror the same split for offer truth:
  - clear product-facing offer explanation
  - full technical contract underneath

### Integration Points
- Primary engine seams for Phase 34:
  - `credit-coach/src/credit_coach/recourse/action_space.py`
  - `credit-coach/src/credit_coach/recourse/offer_optimization.py`
  - `credit-coach/src/credit_coach/data/schema.py`
- Important downstream consumers to keep aligned:
  - `credit-coach/src/credit_coach/coaching/messaging.py`
  - `credit-coach/src/credit_coach/cli/run_recourse.py`
  - `credit-coach/src/credit_coach/coaching/planner.py`
  - `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`

</code_context>
