# Curated Demo Handoff

Bu dokuman website tarafinda pilot ve proof handoff dilini sabitler.

Ana ilke:

- proof without leakage

Yani:

- confidence ve governance goster
- internal debug surface gosterme

## 1. Demo'dan Pilot'a Gecis

Curated walkthrough sonunda artik engine-owned Phase 44 baseline referans verilir:

- `pilot_refresh_manifest.json`
- `artifact_qa_summary.json`
- `release_smoke_summary.json`
- `decision_explanation_pack.json`

Website bunlari yeniden uretmez.
Sadece kontrollu narrative ile handoff eder.

## 2. Operator Handoff Sirasi

Curated handoff icin siralama:

1. `/demo`
2. `/proof`
3. pilot refresh status
4. dual-lane gate okuma
5. institution-facing explanation pack

## 3. Hangi Truth'ler One Cikar?

Website handoff'ta one cikabilecek truth'ler:

- deterministic decision baseline
- repeatable refresh cadence
- artifact QA pass veya watchlist
- portfolio smoke pass veya watchlist
- institution overlay support

## 4. Hangi Truth'ler Icerde Kalir?

Dis handoff'ta asla one cikmaz:

- `NEEDS_REVIEW`
- raw gate trace
- candidate policy comparison tablolarinin tumu
- operator-only notes
- internal defect detail

## 5. Explanation Pack Kullanimi

Institution-facing handoff'ta explanation pack su sorulari cevaplar:

- karar ne?
- kisa gerekce ne?
- hangi numeric driver'lar etkili?
- hangi kosulda karar iyilesebilir?
- beklenen readiness nedir?

Bu artifact:

- legal opinion degildir
- compliance automation degildir
- institution review yerine gecmez

## 6. Bounded Story

Dogru ton:

- controlled
- governed
- repeatable
- versioned
- bounded

Kacinilacak ton:

- fully compliant
- autonomous underwriting
- real-time integrated
- production-ready at scale

## 7. Related Docs

- [PILOT_READINESS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/PILOT_READINESS.md)
- [PILOT_EXECUTION_GUIDE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/PILOT_EXECUTION_GUIDE.md)
- [DECISION_EXPLANATION_PACK.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/DECISION_EXPLANATION_PACK.md)
