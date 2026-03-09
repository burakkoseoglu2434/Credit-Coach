# CREDIT COACH FINTECH HARDENING - SPRINT 7 RAPORU

## 0) Kapsam
Sprint: `Sprint-7 (Post-Backlog Hardening)`  
Tarih: `2026-03-07`  
Odak:
1. DiCE runtime fallback oranini azaltma
2. Production smoke gate otomasyonu
3. `datetime.utcnow` warning cleanup

---

## 1) Yapilan Degisiklikler (Dosya Bazli)

### 1.1 DiCE runtime hardening
- `credit-coach/src/credit_coach/recourse/dice_baseline.py`
  - DiCE method listesi deterministic hale getirildi.
  - Version-uyumlu `generate_counterfactuals` parametre secimi eklendi (`query_instance` / `query_instances`).
  - Tek method fail olursa otomatik method-forward denemesi eklendi (`random -> genetic -> kdtree`).
  - Telemetry genisletildi:
    - `exception_message`
    - `attempted_method_count`
    - `attempted_methods`
    - `method_attempts`

- `credit-coach/src/credit_coach/cli/run_recourse.py`
  - `enable_method_fallback` config baglantisi eklendi.
  - `metrics.json` icin `dice_attempted_method_count` alani eklendi.

- `credit-coach/configs/recourse.yaml`
  - `dice.enable_method_fallback: true` eklendi.

### 1.2 Production smoke gate CLI
- `credit-coach/src/credit_coach/cli/run_production_smoke.py` (yeni)
  - Latest artifactlerden gate bazli PASS/FAIL degerlendirmesi:
    - `G1_MODEL_BACKTEST`
    - `G2_FAIRNESS`
    - `G3_ROBUSTNESS`
    - `G4_MONITORING_TELEMETRY`
    - `G5_SECURITY_AUDIT`
  - Audit hash chain verifikasyonu entegrasyonu.
  - Cikti dosyalari:
    - `production_smoke_report.csv`
    - `production_smoke_report.json`
  - Run metric:
    - `overall_status` (`GO` / `NO_GO`)

### 1.3 UTC warning cleanup
- `credit-coach/src/credit_coach/utils/time.py` (yeni)
  - `utc_now()`
  - `utc_now_naive()`

- `credit-coach/src/credit_coach/data/schema.py`
  - Tum `default_factory=datetime.utcnow` alanlari `utc_now` ile guncellendi.

- `credit-coach/src/credit_coach/storage/models.py`
  - ORM `created_at` default'lari `utc_now_naive` ile guncellendi.

- `credit-coach/src/credit_coach/macro/sources.py`
  - Mock snapshot zamani `utc_now()` ile guncellendi.

### 1.4 Dokumantasyon guncellemeleri
- `credit-coach/README.md`
  - Yeni `run_production_smoke` komutu eklendi.
  - DiCE runtime fallback notu eklendi.
- `credit-coach/docs/PROD_RUNBOOK.md`
  - Production smoke gate adimi eklendi.
- `credit-coach/docs/RELEASE_GATES.md`
  - Dry-run prosedurune `run_production_smoke` eklendi.

### 1.5 Yeni/Genisletilen testler
- `credit-coach/tests/test_dice_adapter_hardening.py`
  - `query_instances` signature uyumluluk testi eklendi.
  - Method-forward fallback testi eklendi.
- `credit-coach/tests/test_production_smoke.py` (yeni)
  - Gate PASS senaryosu
  - Gate FAIL senaryosu

---

## 2) Calistirilan Komutlar

1. Hedefli testler:
```bash
cd credit-coach && pytest -q tests/test_dice_baseline.py tests/test_dice_adapter_hardening.py tests/test_production_smoke.py tests/test_audit_chain.py tests/test_validator_ci.py
```

2. Tam test suiti:
```bash
cd credit-coach && pytest -q
```

3. Recourse + DiCE runtime dogrulama:
```bash
cd credit-coach && python -m credit_coach.cli.run_recourse --customer_id demo --row_index 5 --base_config configs/default.yaml --model_config configs/model.yaml --recourse_config configs/recourse.yaml --causality_config configs/causality.yaml --safety_config configs/safety.yaml --macro_config configs/macro.yaml
```

4. Release dry-run + smoke:
```bash
cd credit-coach && python -m credit_coach.cli.run_benchmark --model_config configs/model.yaml --window_size 3 --window_step 1 --last_k_windows 3
cd credit-coach && python -m credit_coach.cli.run_fairness --base_config configs/default.yaml --model_config configs/model.yaml --macro_config configs/macro.yaml --group_feature home_ownership
cd credit-coach && python -m credit_coach.cli.run_monitoring --base_config configs/default.yaml --monitoring_config configs/monitoring.yaml
cd credit-coach && python -m credit_coach.cli.run_production_smoke
```

---

## 3) Test Sonuclari

1. Hedefli testler: `9 passed`
2. Tam suiti: `74 passed`
3. Onemli fark:
   - `datetime.utcnow` kaynakli warningler temizlendi (test ozetinde warning yok).

---

## 4) Cikti ve KPI Gozlemleri

### 4.1 DiCE runtime sonucu
- Recourse Run ID: `20260307_012517_59ec24_5b6e48`
- `metrics.json`:
  - `dice_backend: "dice"`
  - `dice_plan_count: 3`
  - `dice_fallback_reason: null`
  - `dice_attempted_method_count: 1`

- `tables/dice_telemetry.json`:
  - `method_requested: "random"`
  - `method_used: "random"`
  - `fallback_reason: null`
  - `attempted_methods: ["random"]`

Not: Onceki runlarda gozlenen `heuristic_fallback_error (TypeError)` durumu bu iterasyonda tekrar edilmedi.

### 4.2 Production smoke sonucu
- Benchmark Run ID: `20260307_012533_1d6868_f276f5`
- Fairness Run ID: `20260307_012535_ecb8c8_b38276`
- Monitoring Run ID: `20260307_012536_07f77f_75140a`
- Smoke Run ID: `20260307_012538_543396_1d849d`

- `production_smoke_report.csv`:
  - G1..G5 tum gate'ler `PASS`
- `metrics.json`:
  - `overall_status: "GO"`
  - `gate_pass_count: 5`
  - `gate_fail_count: 0`
  - `audit_issue_count: 0`

---

## 5) Acilan Riskler ve Teknik Borc

1. Ortamda matplotlib/font cache write izinleri olmadigi icin calisma sirasinda cache warningleri goruluyor (`MPLCONFIGDIR` ile ortamsal duzeltme onerilir).
2. Telemetry default olarak `disabled`; production ortamda endpoint ve policy aktiflenmeden exporter success gorulmez.
3. DiCE method-forward fallback devrede; production benchmark ile method bazli kalite/perf trade-off raporlanmali.

---

## 6) Sonraki Adim Giris Kosullari

1. `run_production_smoke --require_telemetry_enabled` ile staging ortamda zorunlu telemetry testinin PASS alinmasi.
2. 1000 musteri batch recourse calismasinda:
   - `dice_backend == dice` orani
   - method bazli latency
   - approval/fairness etkisi
   metriklerinin olculmesi.
