# Curated Demo Handoff

Bu dokuman, yapilandirilmis demo intake alanlarini operator tarafinda tekrar edilebilir bir institution-specific walkthrough akisina cevirir.

Amac:

- `institutionType`, `portfolioFocus`, `demoTrack`, `timeline`, `dataReadiness` alanlarini anlamli bir demo kurgusuna baglamak
- mevcut `/demo` ve `/proof` yuzeylerinden disari tasmamak
- trust ve traceability cizgisini korumak

Bu dokuman yeni urun capability tanimlamaz. Mevcut urun yuzeylerini curate eder.

Engine-side pilot package referanslari:

- [PILOT_EXECUTION_GUIDE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/PILOT_EXECUTION_GUIDE.md)
- [PILOT_PACKAGE_SCHEMA.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/PILOT_PACKAGE_SCHEMA.md)

## 1. Intake'ten Demo'ya Gecis Kurali

Her ciddi inbound demo talebi icin operator su alanlari okur:

- `institutionType`
- `portfolioFocus`
- `demoTrack`
- `timeline`
- `dataReadiness`

Sonra walkthrough'u su sirayla kurar:

1. ana demo track secilir
2. `/demo` icindeki bolum sirasi belirlenir
3. `/proof` ile trust ve watchlist kapanisi eklenir
4. net bir next step tanimlanir

Eger buyer conversation pilot scoping'e ilerliyorsa, next step website checklist'i degil engine-owned `pilot package` olur.

## 2. Demo Track Haritasi

| demoTrack | Ne zaman secilir | Route sirasi | Ana artifact'ler | Next step |
|-----------|------------------|--------------|------------------|-----------|
| `recovery-baseline` | Buyer once tek dosya ve kontrollu toparlanma hikayesini gormek istiyorsa | `/demo` customer -> `/demo` portfolio -> `/proof` | `single-customer-roadmap`, `portfolio-batch-summary`, `product-confidence-snapshot` | Focused walkthrough veya proof review |
| `portfolio-proof` | Buyer once portfoy etkisi ve proof guvenini gormek istiyorsa | `/demo` portfolio -> `/proof` -> `/demo` customer | `portfolio-batch-summary`, `product-confidence-snapshot`, `single-customer-roadmap` | Proof review veya pilot scoping call |
| `offer-and-learning` | Buyer teklif ve future learning tarafini ayni narrative icinde gormek istiyorsa | `/demo` offer -> `/demo` learning -> `/proof` | `offer-optimization`, `outcome-ingestion`, `product-confidence-snapshot` | Pilot scoping call veya deeper product walkthrough |

## 3. Intake Alanlarinin Yorumlanmasi

### institutionType

- `bank`
  - dil: governance, rollout discipline, multi-team fit
  - vurgu: `/proof` ve portfolio section
- `lender`
  - dil: denied applicant recovery, controlled recovery, offer performance
  - vurgu: customer + portfolio + offer
- `fintech`
  - dil: speed to pilot, workflow clarity, focused deployment lane
  - vurgu: customer + proof
- `servicer`
  - dil: recovery operations, outcome logging, learning discipline
  - vurgu: portfolio + learning + proof

### portfolioFocus

`portfolioFocus` operator icin anlatim ornegini belirler; yeni veri yaratmaz.

Kural:

- mevcut artifact'ler degismez
- ornekler ve aciklamalar focus alanina gore secilir
- urun hikayesi halen denied or near-threshold recovery wedge'inde kalir

### timeline

- `0-30`
  - hizli scoping ve controlled pilot lane vurgulanir
- `30-90`
  - curation + proof + ops baseline birlikte anlatilir
- `90-plus`
  - deployment ve operator readiness tarafi daha belirgin ele alinir
- `exploring`
  - once wedge, proof, ve trust cizgisi anlatilir; somut pilot tarihi zorlanmaz

### dataReadiness

- `curated-sample`
  - curated story kullanilir
  - disclaimer mutlaka gorunur
- `sample-export`
  - current product surfaces gosterilir, sonra hangi institution-specific curation'in mumkun oldugu anlatilir
- `production-like`
  - current product surfaces + pilot scoping + ops baseline birlikte ele alinir

## 4. Route ve Bolum Sirasi

### `/demo`

Kullanilabilecek bolumler:

- customer
- portfolio
- offer
- learning

Operator, intake'e gore bolum sirasi degistirebilir; fakat section icerigi degistirmez.

Default section-order guardrail:

- customer -> portfolio -> offer -> learning

### `/proof`

Her curated flow su proof sinyallerini korumali:

- buyer verdict
- `safe to pilot`
- `controlled rollout`
- `institution-ready safeguards`
- benchmark panel
- watchlist

`/proof`, curated flow'un trust kapanisidir. Cikartilmaz.

## 5. Trust Cues Korumasi

Her curated walkthrough'ta su UI cue'lari gorunur kalmali:

- `/demo` uzerinde `Representative product preview — not real customer data`
- `/demo` uzerinde business-first executive hierarchy
- `/proof` uzerinde `safe to pilot`
- `/proof` uzerinde watchlist we would not hide before a pilot

Curated anlatim bu cue'lari gizleyemez veya yumusatamaz.

## 6. Artifact Haritasi

Curated demo sadece bu mevcut artifact'lere dayanir:

- `single-customer-roadmap`
- `portfolio-batch-summary`
- `offer-optimization`
- `outcome-ingestion`
- `product-confidence-snapshot`

Gerektiginde destekleyici artifact referanslari:

- `action-realism`
- `behavior-aware`
- `trajectory`
- `off-policy-evaluation`
- `pilot_package_manifest`
- `pilot_guardrails`
- `portfolio_validation_summary`
- `product_confidence_snapshot`

Kural:

- yeni artifact uydurma
- mevcut snapshot sinirinin disina cikma
- buyer-facing story'yi artifact reality'sinden koparma
- pilot scoping asamasinda engine-owned pilot package'i kaynak almadan yeni integration hikayesi kurma

## 7. Operator Checklist

Walkthrough oncesi:

- intake alanlari dolu mu
- `demoTrack` secili mi
- `timeline` gercekci mi
- `dataReadiness` posture'u net mi
- persistence posture pilot icin uygunsa database-backed mi

Walkthrough sirasinda:

- `/demo` disclaimer gorunur mu
- section sirasi intake'e gore anlamli mi
- `/proof` ile trust kapanisi yapildi mi
- watchlist acikca gosterildi mi

Walkthrough sonrasi:

- next step secildi mi
- follow-up owner belli mi
- pilot scoping gerekiyorsa `PILOT_READINESS.md` baz alindi mi

## 8. Next Step Secimi

Curated walkthrough sonunda operator yalnizca bir sonraki adimi onerir:

- `Focused walkthrough`
  - buyer once product flow'u anlamak istiyor
- `Proof review`
  - buyer once guven ve benchmark okumasini derinlestirmek istiyor
- `Pilot scoping call`
  - buyer ciddi timeline ve ops sorularina gecmeye hazir
  - engine-side `run_pilot_integration` ve `pilot package` akisi anlatilmaya hazir

Next step secimi su sinyallerle uyumlu olmali:

- `timeline`
- `dataReadiness`
- `/proof` verdict ve watchlist

## 9. Scope Guardrail

Bu handoff pack:

- mevcut `/demo` ve `/proof` capability'sine dayanir
- trust ve provenance'i korur
- institution-specific curation'i operator tarafinda tekrar edilebilir hale getirir

Bu handoff pack su anlama gelmez:

- live institution data baglandi
- self-serve pilot workspace acildi
- auth veya CRM tamamlandi
- engine package disinda ayri bir website pilot evaluation stack var
