# CREDIT COACH FINTECH HARDENING - IMPLEMENTATION BACKLOG + SPRINT PLAN

## Surum
- Dokuman surumu: `v1.0`
- Tarih: `2026-03-07`
- Kapsam: `Uretim sertlestirme + derin entegrasyon + governance`
- Baglayicilik: `Agent bu dokuman disina cikamaz`

---

## 1) Amac
Bu planin amaci, mevcut Credit Coach kod tabanini tez prototipinden fintech urun seviyesine tasimak icin:
1. Uygulanabilir backlog olusturmak.
2. Sprint bazli is parcaciklarini netlestirmek.
3. Her adim icin test ve acceptance kriterlerini zorunlu kilmak.

Bu plan, su odak alanlarini kapatir:
1. Uretim sertlestirme
2. XGBoost/SHAP/DiCE entegrasyon derinligi
3. Stress/fairness/backtesting derinligi
4. Guvenlik, audit ve operasyonel izleme

---

## 2) Baslangic Durumu (As-Is)
Mevcut raporlara gore:
1. 12 haftalik temel akis kodlanmis ve calisir durumda.
2. Hardening iterasyonunda ek guclendirmeler yapildi.
3. Hala acik kalan bosluklar:
   - DiCE tarafinda fallback bagimliligi
   - Robust recourse ve sequential recourse derinliginin sinirli olmasi
   - Backtesting kapsaminda zaman pencereli karar kalitesi raporunun yetersiz olmasi
   - API tarafinda rate-limit, key rotation, imzali audit zinciri eksigi
   - Monitoring tarafinda Prometheus/OpenTelemetry sink eksigi

---

## 3) Basari Kriteri (Target KPI Contract)

## 3.1 Model ve recourse KPI
1. `AUC >= 0.90`
2. `Brier <= 0.12`
3. `Recourse validity >= 0.85`
4. `Median action_count <= 4`
5. `Median plan_cost <= tanimli urun butcesi`
6. `Shock min_reliability >= 0.70`

## 3.2 Fairness KPI
1. `approval_gap <= 0.08`
2. `adverse_impact_ratio >= 0.80`
3. `equalized_odds_gap <= 0.08`

## 3.3 Operasyon KPI
1. `p95 /score latency <= 300 ms`
2. `Alert MTTD <= 15 dk`
3. `Audit log coverage = 100%` (score + plan + policy kararlari)

---

## 4) Baglayici Uygulama Kurallari
1. Tum degisiklikler config-first olacak (`configs/*.yaml`).
2. Her backlog maddesinde en az bir otomatik test eklenecek.
3. Her sprint sonunda calisan komut + artifact + metrics kaydi zorunlu.
4. Acceptance kriteri saglanmayan is `DONE` sayilamaz.
5. Security maddeleri icin insecure demo davranislari production profilinde kapali olacak.
6. DB/artefact degisimlerinde backward uyumluluk veya migration plani yazilacak.

---

## 5) Sprint Takvimi (6 Sprint / 12 Hafta)
1. `Sprint-1 (Hafta 1-2)`: Security baseline + API sertlestirme
2. `Sprint-2 (Hafta 3-4)`: Gercek XGBoost/SHAP/DiCE uyumluluk sertlestirme
3. `Sprint-3 (Hafta 5-6)`: Robust recourse (uncertainty + scenario aware)
4. `Sprint-4 (Hafta 7-8)`: Sequential recourse + dynamic coaching policy
5. `Sprint-5 (Hafta 9-10)`: Backtesting + fairness stress lab
6. `Sprint-6 (Hafta 11-12)`: Ops monitoring, release gate, runbook ve freeze

---

## 6) Detayli Backlog

## Epic A - Security ve Compliance Hardening

### A1 - API rate limiting ve abuse korumasi (P0)
- Hedef: `score/demo` ve ilerideki endpointlerde token bazli rate-limit.
- Degisecek alanlar:
  - `credit-coach/src/credit_coach/api/main.py`
  - `credit-coach/src/credit_coach/api/auth.py`
  - `credit-coach/configs/security.yaml` (yeni)
- Teslim:
  1. Token bucket veya fixed window limiter
  2. Limit asiminda 429 + standard error body
  3. Config ile endpoint bazli limit
- Test:
  - `tests/test_api_rate_limit.py` (yeni)
- Acceptance:
  1. 60 sn pencerede limit asiminda deterministik 429
  2. Gecerli token ve limit altinda 200

### A2 - Audit event hash chain (P0)
- Hedef: plan/score/policy kararlarinin degistirilemez audit izi.
- Degisecek alanlar:
  - `credit-coach/src/credit_coach/storage/models.py`
  - `credit-coach/src/credit_coach/storage/repository.py`
  - `credit-coach/src/credit_coach/utils/hashing.py`
- Teslim:
  1. Her event icin `event_hash` ve `prev_hash`
  2. Chain verification CLI (`run_audit_verify.py`)
- Test:
  - `tests/test_audit_chain.py` (yeni)
- Acceptance:
  1. Araya sahte event eklendiginde verify fail etmeli
  2. Normal akista verify pass etmeli

### A3 - Secret rotation ve token policy (P0)
- Hedef: tek token yerine key set + expiry + rotation policy.
- Degisecek alanlar:
  - `credit-coach/src/credit_coach/api/auth.py`
  - `credit-coach/configs/security.yaml`
- Teslim:
  1. Active + next key modeli
  2. Expired key reject
- Test:
  - `tests/test_auth_rotation.py` (yeni)
- Acceptance:
  1. Rotation sonrasi eski key grace period disinda reddedilmeli

---

## Epic B - Model/XAI/DiCE Derin Entegrasyon

### B1 - XGBoost production profile ve deterministic training (P0)
- Hedef: fallback yerine XGBoost primary, fallback sadece policy ile.
- Degisecek alanlar:
  - `credit-coach/src/credit_coach/model/train.py`
  - `credit-coach/configs/model.yaml`
- Teslim:
  1. Seed sabitleme
  2. Monotonic constraints config destegi
  3. Fallback nedeni metrik kaydi
- Test:
  - `tests/test_model_xgb_profile.py` (yeni)
- Acceptance:
  1. XGB izinli ortamda backend `xgboost` olmali
  2. Fallback olursa reason kodu zorunlu

### B2 - SHAP reliability pack (P1)
- Hedef: local/global SHAP kalitesini ve stabilitesini izlemek.
- Degisecek alanlar:
  - `credit-coach/src/credit_coach/xai/shap_local.py`
  - `credit-coach/src/credit_coach/xai/shap_global.py`
  - `credit-coach/src/credit_coach/cli/run_recourse.py`
- Teslim:
  1. SHAP baseline drift kontrolu
  2. Explainability confidence skoru
- Test:
  - `tests/test_shap_stability.py` (yeni)
- Acceptance:
  1. Ayni inputta katkilar tolerans icinde tekrar uretilebilmeli

### B3 - DiCE adapter hardening (P0)
- Hedef: heuristic fallback oranini ciddi azaltmak.
- Degisecek alanlar:
  - `credit-coach/src/credit_coach/recourse/dice_baseline.py`
  - `credit-coach/src/credit_coach/recourse/generator.py`
  - `credit-coach/src/credit_coach/data/schema.py`
- Teslim:
  1. Feature type adapter (continuous/categorical) iyilestirme
  2. DiCE method secimi (`random/genetic/kdtree`) config ile
  3. Fallback telemetry: neden/feature bazli log
- Test:
  - `tests/test_dice_adapter_hardening.py` (yeni)
- Acceptance:
  1. Benchmark veri setinde fallback orani <= %20
  2. DiCE validity >= %70 (baseline hedef)

---

## Epic C - Robust ve Sequential Recourse

### C1 - Robust recourse objective (P0)
- Hedef: tek nokta PD yerine scenario dagilimi altinda plan secimi.
- Degisecek alanlar:
  - `credit-coach/src/credit_coach/recourse/generator.py`
  - `credit-coach/src/credit_coach/macro/reliability.py`
  - `credit-coach/src/credit_coach/safety/validator.py`
- Teslim:
  1. Worst-case veya CVaR tabanli recourse skoru
  2. `robust_score` kolonunun planlara yazilmasi
- Test:
  - `tests/test_robust_recourse.py` (yeni)
- Acceptance:
  1. Secilen plan normal + stress modda dominance gostermeli

### C2 - Sequential recourse planner (P0)
- Hedef: tek atim yerine 4-12 haftalik aksiyon zinciri optimize etmek.
- Degisecek alanlar:
  - `credit-coach/src/credit_coach/coaching/loop.py`
  - `credit-coach/src/credit_coach/coaching/planner.py`
  - `credit-coach/src/credit_coach/coaching/reviewer.py`
- Teslim:
  1. Multi-step state transition
  2. Her hafta recourse refresh ve policy check
  3. Dropout/noise simule eden progress modeli
- Test:
  - `tests/test_sequential_recourse.py` (yeni)
- Acceptance:
  1. 4 haftalik simulasyonda stagnation goruldugunde replan tetiklenmeli

---

## Epic D - Backtesting + Fairness Stress Lab

### D1 - Rolling window backtesting (P0)
- Hedef: zaman pencereli performans ve stability.
- Degisecek alanlar:
  - `credit-coach/src/credit_coach/cli/run_benchmark.py`
  - `credit-coach/src/credit_coach/evaluation/metrics.py`
  - `credit-coach/src/credit_coach/evaluation/tables.py`
- Teslim:
  1. Rolling window AUC/PR-AUC/Brier trend
  2. Window bazli recourse validity
- Test:
  - `tests/test_backtesting_windows.py` (yeni)
- Acceptance:
  1. Son 3 window ortalamasi KPI contract altina dusmemeli

### D2 - Stress x Fairness matrix (P1)
- Hedef: makro senaryo + grup bazli etkilerin ortak analizi.
- Degisecek alanlar:
  - `credit-coach/src/credit_coach/cli/run_fairness.py`
  - `credit-coach/src/credit_coach/macro/shock_sim.py`
  - `credit-coach/src/credit_coach/ops/monitoring.py`
- Teslim:
  1. Senaryo bazli approval_gap ve equalized_odds_gap
  2. `fairness_stress_matrix.csv`
- Test:
  - `tests/test_fairness_stress_matrix.py` (yeni)
- Acceptance:
  1. High-stress senaryoda fairness sapmasi alarm esigini asarsa HIGH alert uretilmeli

---

## Epic E - Monitoring, SRE, Release Readiness

### E1 - Prometheus/OpenTelemetry exporter (P0)
- Hedef: monitoring ozetini dosya yerine metric sink'e aktarmak.
- Degisecek alanlar:
  - `credit-coach/src/credit_coach/ops/monitoring.py`
  - `credit-coach/src/credit_coach/cli/run_monitoring.py`
  - `credit-coach/src/credit_coach/ops/telemetry.py` (yeni)
- Teslim:
  1. `approval_rate`, `avg_risk_margin`, `max_psi`, `fairness_gap`, `alert_count` metric export
  2. Exporter on/off config
- Test:
  - `tests/test_telemetry_export.py` (yeni)
- Acceptance:
  1. Mock endpoint'e metric push basarili olmali

### E2 - Production runbook + release gates (P0)
- Hedef: release oncesi standart kontrol listesi.
- Degisecek alanlar:
  - `credit-coach/README.md`
  - `credit-coach/docs/PROD_RUNBOOK.md` (yeni)
  - `credit-coach/docs/RELEASE_GATES.md` (yeni)
- Teslim:
  1. Incident response adimlari
  2. Rollback stratejisi
  3. Go/No-Go gate formu
- Test:
  - Dokuman test: release checklist dry-run
- Acceptance:
  1. Gate maddelerinin tamami dogrulanmadan release etiketi verilemez

---

## 7) Sprint Bazli Dagilim

## Sprint-1 (Hafta 1-2)
- Isler: `A1, A2, A3`
- Cikti:
  1. `security.yaml`
  2. Rate-limitli API
  3. Audit hash chain + verify komutu
- Sprint test komutu:
  - `cd credit-coach && pytest -q tests/test_auth.py tests/test_api_rate_limit.py tests/test_audit_chain.py`
- Sprint gate:
  1. Kritik guvenlik testleri %100 pass

## Sprint-2 (Hafta 3-4)
- Isler: `B1, B2, B3`
- Cikti:
  1. XGBoost primary profile
  2. SHAP stability report
  3. DiCE adapter hardening raporu
- Sprint test komutu:
  - `cd credit-coach && pytest -q tests/test_model_xgb_profile.py tests/test_shap_stability.py tests/test_dice_adapter_hardening.py`
- Sprint gate:
  1. Fallback orani hedefe yaklasmali

## Sprint-3 (Hafta 5-6)
- Isler: `C1`
- Cikti:
  1. Robust recourse skorlamasi
  2. Yeni plan secim tablosu
- Sprint test komutu:
  - `cd credit-coach && pytest -q tests/test_robust_recourse.py tests/test_validator_ci.py`
- Sprint gate:
  1. Stress altinda plan siralamasi istikrarli olmali

## Sprint-4 (Hafta 7-8)
- Isler: `C2`
- Cikti:
  1. Sequential planner v1
  2. Dynamic replan trigger metrikleri
- Sprint test komutu:
  - `cd credit-coach && pytest -q tests/test_sequential_recourse.py tests/test_coaching_progress.py`
- Sprint gate:
  1. Replan mekanizmasi hedef senaryolarda calismali

## Sprint-5 (Hafta 9-10)
- Isler: `D1, D2`
- Cikti:
  1. Rolling backtest report
  2. Fairness stress matrix
- Sprint test komutu:
  - `cd credit-coach && pytest -q tests/test_backtesting_windows.py tests/test_fairness_stress_matrix.py tests/test_metrics.py`
- Sprint gate:
  1. KPI contract ihlali varsa otomatik FAIL

## Sprint-6 (Hafta 11-12)
- Isler: `E1, E2`
- Cikti:
  1. Telemetry exporter
  2. Prod runbook + release gates
- Sprint test komutu:
  - `cd credit-coach && pytest -q tests/test_telemetry_export.py tests/test_monitoring.py`
- Sprint gate:
  1. Go/No-Go formu PASS olmadan release yok

---

## 8) Global Acceptance Checklist
1. Tum P0 backlog maddeleri tamamlandi.
2. Testler:
   - `cd credit-coach && pytest -q` tam yesil
3. KPI contract:
   - Model, fairness, reliability, latency targetlari saglandi
4. Guvenlik:
   - Rate limit, token rotation, audit chain aktif
5. Operasyon:
   - Monitoring alarmlari + telemetry sink calisir
6. Governance:
   - Backtesting ve stress/fairness raporlari release paketinde
7. Dokumantasyon:
   - Runbook + release gate + update raporu tamam

---

## 9) Raporlama Sozlesmesi (Her Sprint Sonu)
Her sprint sonunda yeni rapor dosyasina asagidaki zorunlu bolumler yazilir:
1. `Yapilan degisiklikler (dosya bazli)`
2. `Calistirilan komutlar`
3. `Test sonuclari`
4. `KPI degisimi`
5. `Acilan riskler ve teknik borc`
6. `Bir sonraki sprint giris kosullari`

Rapor isim standardi:
- `CREDIT_COACH_FINTECH_HARDENING_SPRINT_<N>_RAPORU.md`

---

## 10) Son Hukum
1. Bu dokuman, fintech hardening evresi icin tek operasyon kaynagidir.
2. Agent bu dokuman disinda is acamaz; once backlog id tanimlamasi yapmalidir.
3. Yeni is eklenmesi gerekiyorsa once bu dokuman revize edilir, sonra kod degisikligine gecilir.

