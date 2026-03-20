# Credit Coach Website Tech Architecture

Bu dokuman, `credit-coach-website` uygulamasinin teknik mimarisini kilitler.

Hedef stack:

- `React`
- `Vite`
- `TypeScript`
- `Tailwind CSS`
- `Express`
- `PostgreSQL`
- `Drizzle ORM`

Bu stack uygundur, ama kritik mimari karari su:

`website backend`, `credit-coach` Python engine'inin yerine gecmeyecek.

Sinir su olacak:

- `credit-coach/` -> model, recourse, KPI, artifact uretimi
- `credit-coach-website/` -> sunum, demo, lead capture, content, proof surface

Pilot-ready buyer handoff baseline'i icin ek dokuman:

- [PILOT_READINESS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/PILOT_READINESS.md)

---

## 1. Mimari Prensipler

Bu website icin 6 temel prensip oneriyorum:

1. `Artifact-first`
Website, Python tarafinda uretilen canonical artifact'leri tuketir; yeni source-of-truth yaratmaz.

2. `Thin backend`
Express katmani hafif kalir; agir business logic Python engine'e tasinmaz.

3. `Static-first V1`
Ilk versiyon static curated demo data ile calisir; canli entegrasyon sonraya birakilir.

4. `Typed contracts`
Frontend, backend ve demo snapshot'lari ortak TypeScript schema'lari ile baglanir.

5. `Content and product separation`
Marketing/content ile demo/proof yuzeyleri ayni sitede olur ama ayni veri modeliyle karismaz.

6. `Brownfield-safe`
Website, mevcut `credit-coach/` artifact yapisini bozmadan onun ustune oturur.

---

## 2. Onerilen Klasor Yapisi

Ben su yapıyı oneriyorum:

```text
credit-coach-website/
  README.md
  TECH_ARCHITECTURE.md
  package.json
  tsconfig.json
  vite.config.ts
  tailwind.config.ts
  postcss.config.js
  index.html
  client/
    src/
      main.tsx
      App.tsx
      pages/
      components/
      sections/
      layouts/
      lib/
      hooks/
      styles/
      data/
  server/
    index.ts
    routes.ts
    db.ts
    storage/
    services/
    middleware/
  shared/
    schema.ts
    demo-schema.ts
    content-schema.ts
  demo-data/
    single_customer_roadmap.json
    batch_summary.json
    candidate_quality_summary.json
    action_realism_summary.json
    behavior_aware_summary.json
    trajectory_summary.json
    offer_optimization_summary.json
    decision_logging_summary.json
    outcome_ingestion_summary.json
    off_policy_evaluation.json
    milestone_acceptance_summary.json
    milestone_acceptance_review.md
  scripts/
    sync-demo-artifacts.ts
  public/
    images/
    icons/
```

Bu yapı sana su avantajlari verir:

- frontend ve backend ayni app icinde ama ayrik kalir
- demo verisi kontrollu sekilde yonetilir
- schema paylasimi kolay olur
- sonradan admin / CMS / API eklemek kolaylasir

---

## 3. Hangi Katman Ne Yapacak

## 3.1 Frontend Katmani

Konum:

- `credit-coach-website/client/src`

Sorumlulugu:

- tum sayfa rendering
- landing ve product anlatimi
- demo center UI
- artifact preview kartlari
- charts, KPI tiles, timelines
- investor ve proof sayfalari

Frontend'in gorevi `hesap yapmak` degil, `gostermek` olmali.

Frontend sadece:

- static content
- backend'den gelen content
- curated demo snapshots
- hafif UI-level transforms

ile calismali.

## 3.2 Backend Katmani

Konum:

- `credit-coach-website/server`

Sorumlulugu:

- contact / demo request form API'leri
- article / case study / content API'leri
- curated demo index endpoint'leri
- gelecekte admin veya internal content flows

Backend'in yapmamasi gerekenler:

- model scoring
- recourse generation
- KPI hesaplama
- fairness / telemetry / release logic

Bunlar `credit-coach/` tarafinda kalmali.

## 3.3 Shared Schema Katmani

Konum:

- `credit-coach-website/shared`

Sorumlulugu:

- frontend ve backend icin ortak tipler
- Zod / schema tabanli request-response contract'lari
- demo snapshot tipleri
- content ve form tipleri

Onerdigim ana schema aileleri:

- `ContactRequest`
- `DemoRequest`
- `InvestorRequest`
- `DemoSnapshotIndex`
- `SingleCustomerDemo`
- `PortfolioDemo`
- `OfferOptimizationDemo`
- `LearningLoopDemo`

## 3.4 Database Katmani

Konum:

- `PostgreSQL` + `Drizzle`

Sorumlulugu:

- lead / contact kayitlari
- demo request kayitlari
- content kayitlari
- article metadata
- case study metadata
- artifact snapshot metadata

DB'ye yazilmamasi gereken sey:

- Python engine'in full run artifact'leri
- batch summary source-of-truth
- roadmap source-of-truth
- model output canonical truth

Yani:

- `DB` = website operational data
- `artifact files` = product / engine evidence data

---

## 4. Veri Nerede Duracak

Bu kisim en kritik yer.

## 4.1 Python Engine Source of Truth

Konum:

- `credit-coach/artifacts/runs/<RUN_ID>/tables/`

Burada kalacak:

- `customer_roadmap.json`
- `batch_summary.json`
- `candidate_quality_summary.json`
- `action_realism_summary.json`
- `behavior_aware_summary.json`
- `trajectory_summary.json`
- `offer_optimization_summary.json`
- `decision_logging_summary.json`
- `outcome_ingestion_summary.json`
- `off_policy_evaluation.json`
- `kpi_contract_snapshot.json`
- `milestone_acceptance_summary.json`
- `release_evidence_pack.json`

Bu dosyalar engine tarafinin canonical truth'u olacak.

## 4.2 Website Demo Data

Konum:

- `credit-coach-website/demo-data/`

Burada duracak:

- website'de gostermek icin secilmis ve normalize edilmis snapshot'lar
- kucultulmus, temizlenmis, demo-uygun veri

Bu veriler:

- engine artifact'lerinden kopyalanir veya turetilir
- ama website icin sabit ve kontrollu tutulur

Bu model neden iyi:

- demoda beklenmedik veri kirilmalari azalir
- tasarim stabil olur
- canli backend'e bagimli olmazsin

## 4.3 Website Operational Data

Konum:

- PostgreSQL

Burada duracak:

- contact form submissions
- demo requests
- investor inquiry submissions
- article metadata
- optional case study metadata
- optional snapshot registry

## 4.4 Shared Static Assets

Konum:

- `credit-coach-website/public`

Burada duracak:

- logos
- icons
- images
- social preview assets

---

## 5. V1 Scope

V1'i gereksiz buyutmeyelim.

Benim tavsiye ettigim `V1` kapsamı:

### Dahil

- `Home`
- `Product`
- `Modules`
- `Demo Center`
- `Investor`
- `Contact`
- static curated demo snapshots
- responsive design
- form submission backend
- simple PostgreSQL lead storage

### V1 Demo Data Sources

- `single_customer_roadmap.json`
- `batch_summary.json`
- `candidate_quality_summary.json`
- `action_realism_summary.json`
- `behavior_aware_summary.json`
- `trajectory_summary.json`
- `offer_optimization_summary.json`
- `decision_logging_summary.json`
- `outcome_ingestion_summary.json`
- `off_policy_evaluation.json`
- `milestone_acceptance_summary.json`

### V1 API'leri

- `POST /api/contact`
- `POST /api/demo-request`
- `GET /api/demo/index`
- `GET /api/demo/:slug`

### V1 DB Tablolari

- `contact_requests`
- `demo_requests`
- `investor_requests`

### V1'de Bilerek Dahil Degil

- auth
- admin panel
- article editor
- live scoring
- live recourse generation
- live artifact browse
- CRM entegrasyonu

Faz 25 notu:

- buyer handoff baseline'i artik dokumante edilmis durumda
- ancak `auth` ve `CRM entegrasyonu` halen V1 scope disindadir
- ciddi pilot posture, uygulama ici login yerine operator-mediated ve controlled-access varsayimi ile tanimlanir

V1'in hedefi:

`serious product website + strong demo surface`

---

## 6. V2 Scope

V2'de sistem genisleyebilir.

### Dahil edilebilecekler

- content admin panel
- article / insights area
- case studies
- gated investor materials
- snapshot registry
- versioned demo catalog
- lightweight analytics dashboard
- live artifact ingestion pipeline
- optional Python bridge API

### V2 API'leri

- `GET /api/articles`
- `POST /api/admin/articles`
- `GET /api/case-studies`
- `GET /api/proof/snapshots`
- `POST /api/admin/snapshots/sync`

### V2 DB Tablolari

- `articles`
- `case_studies`
- `demo_snapshots`
- `snapshot_artifacts`
- `page_modules`
- `admin_users` (eger auth eklenirse)

V2'in hedefi:

`website'den productized proof platform'una gecis`

---

## 7. Frontend Route Plani

Ilk route yapisi su olabilir:

- `/`
- `/product`
- `/modules`
- `/demo`
- `/proof`
- `/investor`
- `/contact`

Demo altinda section-based veya nested route da kullanabilirsin:

- `/demo/customer`
- `/demo/portfolio`
- `/demo/offers`
- `/demo/learning`

Ama V1'de tek `/demo` altinda tab'li bir sayfa bence daha iyi.

---

## 8. Component Seviyesinde Mimari

Frontend component agaci su mantikla kurulabilir:

### Layout

- `SiteShell`
- `MainNav`
- `Footer`

### Shared UI

- `MetricTile`
- `SectionHeader`
- `ArtifactCard`
- `BadgeRow`
- `Timeline`
- `ChartCard`
- `CTASection`

### Demo Components

- `CustomerRoadmapPreview`
- `BatchKpiGrid`
- `RecommendationQualityPanel`
- `OfferOptimizationPanel`
- `LearningLoopPanel`
- `GovernancePanel`

### Investor Components

- `ProblemValueSection`
- `MilestoneStrip`
- `BuildProofSection`
- `ExpansionPathSection`

---

## 9. Veri Akinin Nasil Isleyecegi

## 9.1 V1 Veri Akisi

```text
credit-coach artifacts
  -> manual / scripted snapshot selection
  -> credit-coach-website/demo-data
  -> frontend demo pages
```

Bu ilk shipping icin en saglikli akistir.

## 9.2 V2 Veri Akisi

```text
credit-coach artifacts
  -> sync script
  -> snapshot metadata in DB
  -> Express API
  -> frontend proof / demo pages
```

Yani V2'de DB artifact'in kendisini degil, metadata'sini tutar.

---

## 10. En Onemli Mimari Sinirlar

Bu projede su 5 seyi karistirmayalim:

1. `Website data` ile `engine artifact truth`
2. `Marketing copy` ile `machine-readable proof`
3. `Express backend` ile `credit-coach Python logic`
4. `Demo snapshot` ile `live production run`
5. `Lead storage DB` ile `ML/output store`

Bu sinirlar korunursa sistem temiz kalir.

---

## 11. Uygulama Sirasi

Benim tavsiye ettigim uygulama sirasi:

### Adim 1

`credit-coach-website` uygulama iskeleti

- package setup
- Vite
- Tailwind
- client/server/shared yapisi

### Adim 2

Core routes

- home
- product
- demo

### Adim 3

Curated demo data integration

- `demo-data/` snapshot'lari
- customer roadmap preview
- batch KPI panels

### Adim 4

Investor + proof pages

### Adim 5

Contact/demo request backend + DB

---

## 12. Benim Net Tavsiyem

Bu teknoloji setiyle ilerleyelim, ama su sekilde:

- `React + Vite + TypeScript + Tailwind` = hemen
- `Express` = hafif API / form / content katmani
- `PostgreSQL + Drizzle` = lead/content metadata icin
- `credit-coach artifact files` = source-of-truth olarak ayni yerde kalmaya devam etsin

Yani nihai karar:

`full-stack TypeScript website` evet

ama

`Python engine'i yeniden Node tarafina tasimak` hayir

---

## 13. Sonraki Dogru Adim

Bu mimariyi baz alip bir sonraki adimda su isi yapabiliriz:

1. `credit-coach-website` iskeletini olusturmak
2. temel package dosyalarini eklemek
3. `Home` ve `Demo Center` ile ilk implementasyona baslamak
