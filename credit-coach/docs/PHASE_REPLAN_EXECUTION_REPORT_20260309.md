# CREDIT COACH Faz Replan Uygulama ve Sonuç Raporu (2026-03-09)

## 1) Amaç
Bu turda hedef, P0→P2 fazlarını yeniden planlayıp uygulama hattını tek bir deney çerçevesinde çalıştırmak, testleri doğrulamak ve 1000 müşteri / 5 seed KPI gate sonucunu objektif olarak raporlamaktı.

## 2) Replan (Uygulama Sırası)
1. Faz 0 (P0): Baseline dondurma + otomatik deney çerçevesi
2. Faz 1 (P0): Reliability gate hizalama
3. Faz 2 (P0): Latency için sync-fast odaklı gate değerlendirmesi
4. Faz 3 (P1): Fairness karar katmanını recourse seçimine gömme
5. Faz 4 (P0): High-risk aksiyon uzayı genişletme
6. Faz 5 (P1): Challenger model matrisi ile karşılaştırma
7. Faz 6 (P0): Release gate (1000x5)

## 3) Bu Turda Uygulanan Kod Değişiklikleri

### 3.1 Fairness guard sağlamlaştırma
Dosya: `src/credit_coach/cli/run_batch_recourse_eval.py`

Yapılanlar:
- Label-aware postprocess fairness guard aktif akışa bağlı çalıştırıldı.
- Guard, yalnızca ihlali gerçekten düşüren demotion adayını kabul edecek şekilde güncellendi.
- Eksik kolon durumlarında (ör. `pd_delta`) fallback default eklenerek guard’ın kırılmadan çalışması sağlandı.
- Guard metrikleri summary çıktısına eklendi:
  - `fairness_guard_demotion_count`
  - `fairness_guard_iteration_count`
  - `fairness_guard_stop_reason`
  - initial/final fairness delta metrikleri

### 3.2 Fairness guard config
Dosya: `configs/experiments/recourse_phaseb_hybrid_v2.yaml`

Yapılanlar:
- `fairness.postprocess_guard` parametreleri aktif:
  - target EO delta / approval gap / recourse success gap
  - demotion ve iteration limitleri
  - minimum lift floor korumaları
  - priority order

### 3.3 Faz otomasyon CLI (baseline + scale)
Dosya: `src/credit_coach/cli/run_phase_experiment_suite.py`

Yapılanlar:
- Tek komutla:
  - Quick run (200 müşteri)
  - Quick smoke gate
  - Scale run (1000 müşteri, çoklu seed)
- Çıktılar:
  - `phase_quick_summary.json`
  - `phase_scale_seed_summary.csv`
  - `phase_scale_aggregate.json`

## 4) Test Çalıştırmaları
Komut:
```bash
pytest -q tests/test_recourse_funnel_kpis.py tests/test_batch_candidate_diversity.py tests/test_validator_ci.py tests/test_production_smoke.py
```
Sonuç:
- `24 passed`

Not:
- İlk koşuda `pd_delta` kolon erişimi nedeniyle 1 test fail verdi.
- Guard’a eksik kolon fallback eklendikten sonra tüm testler geçti.

## 5) Faz Deney Koşusu (Bu Tur)
Ana suite run:
- `run_id`: `20260309_185511_25dce1_5dc05b`

### 5.1 Quick (200) sonucu
- quick batch run_id: `20260309_185513_b76dca_fb1355`
- quick smoke run_id: `20260309_185520_79e46c_15161e`
- durum: `FAIL`
- fail check: `recourse_success_gap`

### 5.2 Scale (1000 x 5 seed) aggregate
- seed_count: `5`
- pass_count: `2`
- mean_denied_to_approved_lift: `0.1463` (hedef >= 0.09, PASS)
- mean_denied_high_risk_lift: `0.1578` (hedef >= 0.03, PASS)
- mean_denied_reliability_violation_rate: `0.1849` (hedef <= 0.40, PASS)
- mean_sync_latency_p95_ms: `450` (hedef <= 500, PASS)
- mean_sync_latency_p99_ms: `450` (hedef <= 2000, PASS)
- mean_equalized_odds_gap_delta: `0.00375` (hedef <= 0.01, PASS)
- mean_fairness_gap_after: `0.0893` (hedef <= 0.10, PASS)
- mean_high_stress_fairness_gap_after: `0.09445` (hedef <= 0.10, PASS)
- mean_error_rate: `0.0` (hedef <= 0.005, PASS)

### 5.3 Seed bazında sonuç
- PASS: seed `42`, `45`
- FAIL: seed `43`, `44`, `46`
- ortak fail deseni: fairness tarafında seed bağımlı dalgalanma

## 6) Faz Bazlı Değerlendirme
1. Faz 0 (Baseline + deney çerçevesi): **Tamamlandı**
2. Faz 1 (Reliability gate): **KPI seviyesinde tamamlandı** (`~0.185`)
3. Faz 2 (Latency sync-fast gate): **KPI seviyesinde tamamlandı** (`p95/p99=450ms`)
4. Faz 3 (Fairness recourse kararına gömme): **Kısmi tamamlandı** (ortalama PASS, seed-bazlı stabil değil)
5. Faz 4 (High-risk aksiyon genişletme): **KPI seviyesinde etkili** (`high-risk lift` belirgin)
6. Faz 5 (Challenger matrix): **Önceki turlarda mevcut, bu turda tekrar koşturulmadı**
7. Faz 6 (Release gate 1000x5): **Tam PASS değil** (`2/5`)

## 7) Kök Neden (Bu Turun Verisine Göre)
1. Ana blokaj artık lift/reliability/latency değil; fairness metriklerinin seed bazında stabil olmaması.
2. Fairness guard bazı seed’lerde `no_improving_candidate` ile duruyor; yani kalan adaylar lift floor bozmadan fairness ihlalini daha da azaltamıyor.
3. `recourse_success_gap` quick koşuda hâlâ kırmızıya düşebiliyor; bu metrik ürün gate’i için kritik kalmaya devam ediyor.

## 8) Sonuç
- Fazların önemli kısmı uygulanmış ve teknik olarak iyileşme var.
- Sistem artık high-risk lift üretebiliyor ve reliability/latency hedeflerinde güçlü.
- Ancak release için gerekli seed-robust fairness stabilitesi henüz yok.
- Bu nedenle bu tur kararı: **NO_GO (kısmi ilerleme, gate tamamlanmadı)**.

## 9) Sonraki Uygulama Odakları
1. Fairness guard’ı global demotion yerine segment-bazlı quota ve per-segment floor ile yeniden optimize etmek.
2. Rerank skoruna `recourse_success_gap` duyarlı dinamik ceza eklemek.
3. Seed-robust tuning için otomatik parametre taraması (guard threshold + priority order + min improvement) ve 1000x5 tekrar.

## 10) Referans Çıktılar
- Suite çıktı dizini:
  - `artifacts/runs/20260309_185511_25dce1_5dc05b/tables/`
- Quick smoke raporu:
  - `artifacts/runs/20260309_185520_79e46c_15161e/tables/production_smoke_report.csv`
