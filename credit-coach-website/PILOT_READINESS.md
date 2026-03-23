# Credit Coach Website Pilot Readiness

Bu dokuman website tarafinda hangi pilot story'nin guvenle anlatilabilecegini tanimlar.

Phase 44 sonrasi dogru pilot story:

- controlled
- governed
- repeatable
- versioned
- bounded

Bu story su iddialari tasimaz:

- live-integrated
- self-serve
- compliance automation
- autonomous adjudication

## 1. Website Ne Gosterebilir?

Proof surface su sinyalleri gosterebilir:

- pilot refresh completed
- policy versioned baseline
- artifact QA passed veya watchlist
- portfolio smoke passed veya watchlist
- artifact completeness
- generation timestamp
- institution overlay availability

Kural:

- proof without leakage

## 2. Website Ne Gostermez?

Dis yuzeyde su alanlar yer almaz:

- `NEEDS_REVIEW`
- internal review queue state
- raw candidate policy tables
- debug metadata
- raw gate trace
- internal QA failure dump

## 3. Safe Vocabulary

Website ve proof surface icin tercih edilen vocabulary:

- `pilot_refresh_completed`
- `artifact_qa_passed`
- `portfolio_smoke_passed`
- `safe_to_pilot`
- `pilot_watchlist`

Kural:

- debug vocabulary dis yuzeye tasinmaz

## 4. Engine Reference

Website artik parallel bir pilot story kurmaz.
Engine tarafinda uretilen Phase 44 baseline'i referans alir.

Ana referanslar:

- [PILOT_EXECUTION_GUIDE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/PILOT_EXECUTION_GUIDE.md)
- [PILOT_PACKAGE_SCHEMA.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/PILOT_PACKAGE_SCHEMA.md)
- [DECISION_EXPLANATION_PACK.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/DECISION_EXPLANATION_PACK.md)

## 5. Honest Pilot Story

Website tarafinda kullanilabilecek ana vaat:

- deterministic decisions
- repeatable pilot refresh
- QA-gated package
- institution-configurable overlays

Acik sinirlar:

- not live-integrated
- not self-serve
- not compliance automation
- not institution policy replacement

## 6. Scope Guardrail

Dogru cumle:

- "We provide a controlled pilot baseline."

Yanlis cumleler:

- "fully compliant"
- "production-grade autonomous decisioning"
- "real-time integrated"
- "institution-ready at scale"
