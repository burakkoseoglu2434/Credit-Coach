# Phase 73: Action Surface Expansion - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-14
**Phase:** 73-action-surface-expansion
**Areas discussed:** Top-k size & selection rule, Tier scope (full vs assisted_full)

---

## Top-k size & selection rule

### Top-k size

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed k=2 | Surface up to 2 actions when ≥2 valid distinct action families exist; otherwise 1 (or 0 in limited/empty-state). Simple, bounded, easy to evaluate against W2a. | ✓ |
| Fixed k=3 | Surface up to 3 actions when that many distinct valid families exist. More diversity but larger payload/narrative surface. | |
| Dynamic up to all valid families | Surface every distinct valid action family from the selected plan, no hard cap. | |

**User's choice:** Fixed k=2

### Selection rule

| Option | Description | Selected |
|--------|-------------|----------|
| Diversity-first, then rank | Pick the current winner unchanged as action #1, fill remaining slots with next-best actions from DISTINCT families (no repeats). | ✓ |
| Pure ranking (top-k by score) | Take the top-k highest-ranked actions regardless of family. | |
| You decide | Claude picks during planning. | |

**User's choice:** Diversity-first, then rank

---

## Tier scope (full vs assisted_full)

### assisted_full cap

| Option | Description | Selected |
|--------|-------------|----------|
| full only | assisted_full stays at exactly 1 action (Phase 72 contract untouched). Top-k=2 applies only to recourse_mode=full. | ✓ |
| full and assisted_full | Raise assisted_full's cap to 2 as well, restricted to existing assisted_full allowlist. | |
| You decide | Claude picks during planning. | |

**User's choice:** full only

### limited tier

| Option | Description | Selected |
|--------|-------------|----------|
| Untouched | limited customers remain empty-state / 0 actions in Phase 73. | ✓ |
| You decide | Claude picks during planning. | |

**User's choice:** Untouched

---

## Claude's Discretion

- Where action-type distribution metrics are published (new artifact vs. new columns/rows in an existing cohort evaluation artifact).
- Whether institution-assisted candidates are eligible to fill action #2 for full-tier customers, vs. restricting to customer-only/behavioral/restructure/adjustment families.
- Exact narrative/output shape for representing a second action.
- Exact field/column naming for the second surfaced action and distribution metrics.

## Deferred Ideas

- Raising assisted_full's action cap above 1 — revisit only after Phase 73's full-tier top-k=2 is proven trust-clean.
- limited-tier / mid-risk actionable surfacing — Phase 75 (Mid-Risk Segment Unlock).
- Multi-step / sequential plan surfacing — Phase 74 (Multi-Step Plan Surfacing).
