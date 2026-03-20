# Credit Coach Website Pilot Readiness

Bu dokuman, `credit-coach-website` icin minimum pilot-ready buyer handoff baseline'ini tanimlar.

Amac:

- bugun neyin hazir oldugunu netlestirmek
- ciddi bir pilot gorusmesinden once neyin tamamlanmasi gerektigini yazmak
- bilincli olarak ertelenen alanlari durustce ayirmak

Bu dokuman tam production maturity iddiasi degildir.

## 1. Hazir Olan Baseline

Bugun repo seviyesinde hazir olanlar:

- `npm run build`
- `npm run start`
- `GET /api/health`
- `POST /api/contact`
- `POST /api/demo-request`
- `POST /api/investor-request`
- `/contact` uzerinden yapilandirilmis demo ve pilot intake
- `/demo` uzerinden buyer-safe product walkthrough
- `/proof` uzerinden `safe to pilot` ve watchlist okuması
- `DATABASE_URL` verilirse PostgreSQL + Drizzle persistence seami

Bu baseline, ciddi bir buyer conversation ve operator-mediated demo handoff icin yeterli cekirdegi saglar.

## 2. Pilot Oncesi Zorunlu Minimumlar

Asagidakiler tamamlanmadan akisi ciddi pilot-ready olarak sunma:

1. `DATABASE_URL` tanimli olmali
2. `npm run db:push` ile guncel schema veritabanina uygulanmali
3. Uygulama production build ile ayaga kalkmali:
   - `npm run build`
   - `npm run start`
4. `GET /api/health` basarili donmeli
5. Demo ve pilot intake talepleri database modunda kalici olarak kaydedilmeli
6. Bir operator sahibi net olmali:
   - inbound talebi kim okuyacak
   - demo track'i kim sececek
   - follow-up'u kim planlayacak
7. Gorusme oncesi curated track secilmeli:
   - recovery baseline
   - portfolio proof
   - offer and learning

## 3. Ortam ve Runtime Kontrati

### Gerekli environment

- `PORT`
  - opsiyonel
  - varsayilan `3000`
- `DATABASE_URL`
  - ciddi pilot handoff icin zorunlu
  - PostgreSQL baglantisi beklenir

### Runtime komutlari

```bash
npm install
npm run build
npm run db:push
npm run start
```

### Health check

```bash
GET /api/health
```

Beklenen donus:

- `ok: true`
- `company: "Kuantitive"`
- `product: "credit-coach"`
- `service: "website"`

## 4. Persistence Posture

Website iki persistence modunda calisabilir:

- `database`
- `memory`

### Database modu

Bu, ciddi pilot handoff icin kabul edilen moddur.

Beklenenler:

- `DATABASE_URL` tanimli
- schema push tamam
- inbound request kayitlari kalici

### Memory modu

Bu mod yalnizca internal demo veya kisa sureli inceleme icin kabul edilebilir.

Memory modu su nedenlerle pilot-ready sayilmaz:

- kalici kayit garantisi vermez
- operator devrinde iz kaybi riski vardir
- buyer handoff icin guvenli bir temel saglamaz

Kural:

- `memory` modu demo-acceptable
- `database` modu pilot-required

## 5. Auth Posture

Bugunku website siniri icinde:

- uygulama ici login yok
- user role modeli yok
- admin panel yok
- self-serve buyer access yok

Bu nedenle mevcut pilot posture su sekilde tanimlanmali:

- operator-mediated
- controlled access
- gerekiyorsa infra veya network katmaninda korunmus

Bu repo bugun auth-ready degil; controlled pilot conversation-ready seviyesindedir.

## 6. Operator Checklist

Pilot benzeri bir buyer handoff oncesi operator su listeyi gecmeli:

- inbound request `demo` tipinde ve yapilandirilmis alanlari dolu mu
- `institutionType`, `portfolioFocus`, `demoTrack`, `timeline`, `dataReadiness` net mi
- persistence modu `database` mi
- `/demo` ve `/proof` yuzeyleri guncel build ile aciliyor mu
- hangi curated track ile gidilecegi secildi mi
- follow-up next step net mi:
  - walkthrough
  - proof review
  - pilot scoping call

## 7. Ready Now / Required / Deferred

### Ready now

- buyer-safe website and demo surfaces
- structured demo intake
- health endpoint
- production build and server start seams
- optional database-backed inbound capture

### Required before pilot

- database-backed persistence
- schema push
- named operator ownership
- curated demo track secimi
- controlled access posture

### Deferred beyond this milestone

- application auth
- admin console
- CRM integration
- institution-specific automated data ingestion
- self-serve pilot workspace

## 8. Scope Guardrail

`OPS-02` bu repo icin minimum buyer handoff baseline'ini kapatir.

Bu, su anlama gelmez:

- "tam production deployment hazir"
- "multi-user access control tamam"
- "institution onboarding otomatik"

Dogru okuma su:

- ciddi buyer handoff icin minimum operasyonel cizgi artik acik
- bundan sonraki genisleme auth, CRM, admin ve daha derin pilot tooling katmanlaridir
