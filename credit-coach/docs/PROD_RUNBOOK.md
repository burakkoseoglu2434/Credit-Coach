# CREDIT COACH PRODUCTION RUNBOOK

## 1) Amac
Bu runbook, Credit Coach sisteminin production operasyonunda:
1. Baslatma oncesi kontrol
2. Gunluk izleme
3. Incident response
4. Rollback proseduru
adimlarini standartlastirmak icin hazirlanmistir.

## 2) Kapsam
Bu dokuman su is akislari icin referanstir:
1. Model train/registry
2. Recourse generation
3. Fairness + stress degerlendirmesi
4. Batch recourse KPI degerlendirmesi
5. Monitoring + telemetry export

## 3) On Kosullar
1. Ortam degiskenleri:
   - `DB_URL`
   - `CREDIT_COACH_API_TOKEN` veya `CREDIT_COACH_API_KEYS_JSON`
   - (Opsiyonel) endpoint scope policy: `configs/security.yaml -> auth.endpoint_scopes`
2. Config dosyalari:
   - `configs/default.yaml`
   - `configs/model.yaml`
   - `configs/recourse.yaml`
   - `configs/macro.yaml`
   - `configs/monitoring.yaml`
   - `configs/security.yaml`
3. Veriler:
   - `data/processed/train.parquet`
   - `data/processed/test.parquet`

## 4) Baslatma Adimlari
1. Sistem saglik kontrolu:
```bash
python -m credit_coach.cli.run_train --dry_run --base_config configs/default.yaml
```
2. Model train:
```bash
python -m credit_coach.cli.run_train --config configs/model.yaml --base_config configs/default.yaml
```
3. Recourse run:
```bash
python -m credit_coach.cli.run_recourse --customer_id demo --row_index 5 --base_config configs/default.yaml --model_config configs/model.yaml --recourse_config configs/recourse.yaml --causality_config configs/causality.yaml --safety_config configs/safety.yaml --macro_config configs/macro.yaml
```
4. Fairness + stress:
```bash
python -m credit_coach.cli.run_fairness --base_config configs/default.yaml --model_config configs/model.yaml --macro_config configs/macro.yaml --group_feature home_ownership
```
5. Shock reliability:
```bash
python -m credit_coach.cli.run_shock --macro_config configs/macro.yaml --model_config configs/model.yaml
```
6. Monitoring + telemetry:
```bash
python -m credit_coach.cli.run_monitoring --base_config configs/default.yaml --monitoring_config configs/monitoring.yaml
```
7. Batch recourse KPI:
```bash
TQDM_DISABLE=1 python -m credit_coach.cli.run_batch_recourse_eval --n_customers 1000 --sample_seed 42
```
8. Production smoke gate:
```bash
python -m credit_coach.cli.run_production_smoke
```

## 5) Telemetry Konfigurasyonu
`configs/monitoring.yaml`:
1. `telemetry.enabled`: true/false
2. `telemetry.mode`: `prometheus` veya `otlp`
3. `telemetry.endpoint_url`: hedef endpoint
4. `telemetry.namespace`: metric prefix
5. `telemetry.labels`: environment/team etiketleri

Uretilen telemetry artifact:
1. `artifacts/runs/<run_id>/tables/telemetry_export.json`

## 6) Gunluk Operasyon Kontrol Listesi
1. `monitoring_summary.csv`:
   - `approval_rate`
   - `avg_risk_margin`
   - `avg_reliability`
   - `fairness_gap`
   - `high_stress_fairness_gap`
   - `max_psi`
2. `monitoring_alerts.csv`:
   - HIGH alert var mi?
3. `telemetry_export.json`:
   - `exported=true` mi?
   - `status` 2xx mi?
4. `production_smoke_report.csv`:
   - Tum gate'ler PASS mi?
   - `G0_BATCH_RECOURSE_KPI` PASS mi?
5. Batch recourse detaylari:
   - `batch_run_manifest.json` (config+data hash)
   - `denied_not_approved_root_causes.csv`
   - `recourse_action_count_distribution.csv`
   - `recourse_cost_percentiles.csv`

## 7) Incident Response
### 7.1 Severity Tanimlari
1. `SEV-1`: Model karar kalitesi veya guvenlik kritik bozulma
2. `SEV-2`: Fairness/stress threshold ihlali
3. `SEV-3`: Telemetry/export gecikmesi

### 7.2 Ilk 15 Dakika
1. Son run artifact klasorunu kilitle (silme/yazma yok).
2. `monitoring_alerts.csv` ve `metrics.json` snapshot al.
3. Olay kaydi ac:
   - baslangic zamani
   - etkilenen moduller
   - ilk semptom

### 7.3 Triage Komutlari
```bash
python -m credit_coach.cli.run_monitoring --base_config configs/default.yaml --monitoring_config configs/monitoring.yaml
python -m credit_coach.cli.run_fairness --base_config configs/default.yaml --model_config configs/model.yaml --macro_config configs/macro.yaml --group_feature home_ownership
python -m credit_coach.cli.run_shock --macro_config configs/macro.yaml --model_config configs/model.yaml
```

## 8) Rollback Proseduru
1. Registry:
   - `artifacts/models/latest.json` dosyasindan onceki versiyona don.
2. Policy:
   - `configs/model.yaml` ve `configs/recourse.yaml` son bilinen stabil profile cek.
3. Verification:
```bash
python -m credit_coach.cli.run_recourse --customer_id demo --row_index 5 --base_config configs/default.yaml --model_config configs/model.yaml --recourse_config configs/recourse.yaml --causality_config configs/causality.yaml --safety_config configs/safety.yaml --macro_config configs/macro.yaml
python -m credit_coach.cli.run_monitoring --base_config configs/default.yaml --monitoring_config configs/monitoring.yaml
```
4. Rollback tamam kriteri:
   - HIGH alert yok
   - gate ihlali yok

## 9) Sonrasi (Postmortem)
1. 24 saat icinde postmortem raporu:
   - root cause
   - etki analizi
   - tekrarini onleyici aksiyonlar
2. Gerekirse `configs/*` threshold update ve test ekleme.
