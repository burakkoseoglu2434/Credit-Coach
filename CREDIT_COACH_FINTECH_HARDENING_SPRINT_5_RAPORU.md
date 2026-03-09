# CREDIT COACH FINTECH HARDENING - SPRINT 5 RAPORU

## 0) Kapsam
Sprint: `Sprint-5 (Hafta 9-10)`  
Backlog maddeleri: `D1 + D2`  
Tarih: `2026-03-07`

Hedefler:
1. D1 - Rolling window backtesting
2. D2 - Stress x fairness matrix

---

## 1) Yapilan Degisiklikler (Dosya Bazli)

### 1.1 D1 - Rolling window backtesting
- `credit-coach/src/credit_coach/evaluation/metrics.py`
  - `compute_rolling_window_recourse_metrics()` eklendi
  - `summarize_last_k_windows()` eklendi
  - Zaman/sira kolonu bazli siralama + kayar pencere metrik hesaplama eklendi

- `credit-coach/src/credit_coach/cli/run_benchmark.py`
  - Rolling parametreleri eklendi:
    - `window_size`
    - `window_step`
    - `last_k_windows`
    - `window_order_col`
  - Son `k` pencere ozet ve gate hesaplamasi eklendi
  - Yeni artifactler:
    - `benchmark_rolling_windows.csv`
    - `benchmark_lastk_summary.csv`

### 1.2 D2 - Fairness stress matrix
- `credit-coach/src/credit_coach/evaluation/fairness.py`
  - `compute_fairness_bundle()` eklendi
  - `build_fairness_stress_matrix()` eklendi
  - Base + her shock scenario icin fairness metrikleri uretimi eklendi

- `credit-coach/src/credit_coach/macro/reliability.py`
  - `scenario_severity()` public hale getirildi
  - `stressed_tau_for_scenario()` public hale getirildi

- `credit-coach/src/credit_coach/cli/run_fairness.py`
  - `--macro_config` parametresi eklendi
  - `fairness_stress_matrix.csv` artifact uretimi eklendi
  - Metrics'e `max_stress_approval_gap` ve `max_high_stress_approval_gap` eklendi

### 1.3 Monitoring entegrasyonu
- `credit-coach/src/credit_coach/ops/monitoring.py`
  - `fairness_stress_df` opsiyonel girisi eklendi
  - `high_stress_fairness_gap` ozet metriği eklendi
  - `high_stress_fairness_gap` threshold asiminda HIGH alert eklendi

- `credit-coach/src/credit_coach/cli/run_monitoring.py`
  - `--fairness_stress_csv` parametresi eklendi
  - Son artifact fallback ile `fairness_stress_matrix.csv` okumasi eklendi

- `credit-coach/configs/monitoring.yaml`
  - `max_high_stress_fairness_gap` esigi eklendi

### 1.4 Evaluation export ve README
- `credit-coach/src/credit_coach/evaluation/__init__.py`
  - Yeni rolling/fairness-stress fonksiyonlari export edildi

- `credit-coach/README.md`
  - D1 ve D2 notlari eklendi

---

## 2) Test Gelistirmeleri

Yeni testler:
1. `credit-coach/tests/test_backtesting_windows.py`
   - Rolling window metrik ciktilarini dogrular
   - Last-k ozet metriklerini dogrular

2. `credit-coach/tests/test_fairness_stress_matrix.py`
   - Base + scenario fairness stress matrix yapisini dogrular

Guncellenen test:
1. `credit-coach/tests/test_monitoring.py`
   - High-stress fairness gap alert davranisini dogrular

---

## 3) Calistirilan Komutlar ve Sonuclar

1. Hedefli D1/D2 testleri:
```bash
cd credit-coach && pytest -q tests/test_backtesting_windows.py tests/test_fairness_stress_matrix.py tests/test_metrics.py tests/test_monitoring.py tests/test_shock_reliability.py
```
Sonuc: `7 passed`

2. Tam regresyon:
```bash
cd credit-coach && pytest -q
```
Sonuc: `65 passed, 9 warnings`

3. Benchmark (rolling windows):
```bash
cd credit-coach && python -m credit_coach.cli.run_benchmark --model_config configs/model.yaml --window_size 3 --window_step 1 --last_k_windows 3
```
Run ID: `20260307_010753_1d6868_aa2dc9`

4. Fairness + stress matrix:
```bash
cd credit-coach && python -m credit_coach.cli.run_fairness --base_config configs/default.yaml --model_config configs/model.yaml --macro_config configs/macro.yaml --group_feature home_ownership
```
Run ID: `20260307_010754_ecb8c8_84d7d3`

5. Shock ve monitoring snapshot:
```bash
cd credit-coach && python -m credit_coach.cli.run_shock --macro_config configs/macro.yaml --model_config configs/model.yaml
cd credit-coach && python -m credit_coach.cli.run_monitoring --base_config configs/default.yaml --monitoring_config configs/monitoring.yaml
```
Run ID (monitoring): `20260307_010800_336318_07efe1`

---

## 4) Uretilen Ciktilar ve Ozet Metrikler

### 4.1 D1 ciktilari
- `benchmark_rolling_windows.csv`
- `benchmark_lastk_summary.csv`

`benchmark metrics.json`:
1. `our_last_k_validity: 1.0`
2. `our_last_k_safe_rate: 1.0`
3. `our_last_k_avg_risk_margin: 0.2823`
4. `our_validity_gate_pass: true`
5. `our_safe_rate_gate_pass: true`
6. `our_risk_margin_gate_pass: true`

### 4.2 D2 ciktilari
- `fairness_stress_matrix.csv`

`fairness metrics.json`:
1. `approval_gap: 0.0883`
2. `equalized_odds_gap: 0.0749`
3. `stress_scenario_count: 4`
4. `max_stress_approval_gap: 0.0883`
5. `max_high_stress_approval_gap: 0.0883`

### 4.3 Monitoring ciktilari
- `monitoring_summary.csv`
- `monitoring_alerts.csv`

`monitoring metrics.json`:
1. `high_stress_fairness_gap: 0.0883`
2. `alert_count: 0`

Not:
- Mevcut esiklere gore high-stress fairness gap alarmi olusmadi (`0.0883 <= 0.10`).
- Alert mekanizmasi testte threshold asimiyla dogrulandi.

---

## 5) Backlog Durumu
Sprint-5 backlog:
1. `D1 - Rolling window backtesting`: Tamamlandi
2. `D2 - Stress x fairness matrix`: Tamamlandi

Sprint gate:
1. Rolling backtesting artifactleri uretiliyor.
2. Fairness stress matrix artifacti uretiliyor.
3. High-stress fairness alert mekanizmasi kod+test ile aktif.
4. Testler yesil (`65 passed`).

---

## 6) Acilan Riskler ve Teknik Borc
1. Fairness stress matrix su an shift-based simule ediliyor; model-level scenario retraining yok.
2. DiCE runtime fallback (`heuristic_fallback_error`) devam ediyor.
3. `datetime.utcnow()` deprecation warningleri devam ediyor.

---

## 7) Sonraki Sprint Giris Kosullari (Sprint-6)
1. D1 ve D2 tamamlandi.
2. Sonraki odak: `E1 + E2` (telemetry/exporter + prod runbook ve release gate).

