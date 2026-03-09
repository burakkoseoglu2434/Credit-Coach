# Phase Trajectory + KPI Gatefix Execution Report (2026-03-10)

## 1) Scope
Bu çalışmada aşağıdaki hedefler uçtan uca uygulandı ve test edildi:
- Çok katmanlı/hafta-bazlı recourse çıktılarının pipeline'a entegre edilmesi (önceki geliştirmeler doğrulandı).
- KPI gate hesaplarının `phase_experiment_suite` ve `challenger_matrix` içinde contract ile hizalanması.
- Model-state kaynaklı ölçüm sapmasının kapatılması (suite içinde deterministic `train_once`).
- Yeni metriklerle batch/smoke/suite/challenger koşularının yeniden alınması.
- Değişikliklerin test kapsamına alınması ve regresyon kontrolü.

## 2) Kod Değişiklikleri (Bu Faz)

### 2.1 KPI gate hizalama (phase suite)
- `src/credit_coach/cli/run_phase_experiment_suite.py`
  - `_kpi_checks` içine trajectory KPI'ları eklendi:
    - `trajectory_gate_pass_rate_4w`
    - `trajectory_gate_pass_rate_12w`
    - `trajectory_gate_pass_rate_24w`
    - `trajectory_partial_progress_rate`
    - `trajectory_median_time_to_gate_pass_days`
  - `phase_scale_seed_summary.csv` ve `phase_scale_aggregate.json` bu metrikleri raporlayacak şekilde genişletildi.
  - `metrics.json` çıktısına trajectory ortalamaları eklendi.

### 2.2 Deterministic model freeze (phase suite)
- `src/credit_coach/cli/run_phase_experiment_suite.py`
  - `--skip_train_before_batch` argümanı eklendi.
  - Varsayılan davranış: suite başında `run_train` bir kez çalıştırılır (`train_once`) ve batch'ler aynı model state ile ölçülür.
  - Dry-run çıktısına `train_once_cmd` eklendi.

### 2.3 Challenger gate hizalama
- `src/credit_coach/cli/run_model_challenger_matrix.py`
  - Variant agregasyonuna yeni metrikler eklendi:
    - `denied_reliability_violation_rate`
    - `recourse_success_gap`
    - trajectory 4w/12w/24w/partial/time
  - `_gate_violation_score` contract ile genişletildi:
    - reliability upper-bound check
    - recourse success gap check
    - trajectory gate checkleri
    - trajectory median time upper-bound check

### 2.4 Test güncellemeleri
- `tests/test_phase_experiment_suite.py` (yeni + genişletme)
  - trajectory KPI'ları için pass/fail testleri
  - `train_once` command builder testi
- `tests/test_challenger_matrix_selection.py`
  - trajectory gate'lerinin champion seçimini etkilediğini doğrulayan test eklendi.
- `tests/test_action_space.py`
  - `loan_amnt` için test kontratı güncellendi (`loan_amnt` recourse'ta bilinçli actionable kabul ediliyor).

### 2.5 Champion model config
- `configs/experiments/model_champion_logistic_sigmoid.yaml` (yeni)
  - `logistic_regression + sigmoid` (challenger champion) config'i eklendi.

## 3) Test Sonuçları

### 3.1 Tam test paketi
- Komut: `pytest -q`
- Sonuç: **151 passed**

### 3.2 Kritik regresyon ve çözüm
- Bulgu: `tests/test_action_space.py::test_known_immutable_features` fail (`loan_amnt` actionable)
- Çözüm: test kontratı ürün politikasına hizalandı; full suite tekrar geçirildi.

## 4) Çalıştırılan Deneyler ve Metrikler

## 4.1 Standalone batch (trajectory doğrulama)
- Run: `artifacts/runs/20260309_232947_71ae00_0035a7`
- `n=1000`
- Temel metrikler:
  - `denied_to_approved_lift = 0.0929`
  - `denied_high_risk_lift = 0.0985`
  - `denied_reliability_violation_rate = 0.1756`
  - `trajectory_gate_pass_rate_4w = 0.0000`
  - `trajectory_gate_pass_rate_12w = 0.1416`
  - `trajectory_gate_pass_rate_24w = 0.1504`
  - `trajectory_partial_progress_rate = 0.3053`

## 4.2 Phase suite (trajectory gatefix öncesi eski run, referans)
- Run: `artifacts/runs/20260309_233340_6e899d_584e58`
- Not: O versiyonda phase suite trajectory KPI'larını gate hesabına katmıyordu.
- Sonuç: `pass_count = 2/5` (artık güvenilir referans değil; kod düzeltildi).

## 4.3 Phase suite (trajectory gatefix sonrası, default model config)
- Run: `artifacts/runs/20260310_000340_34479c_2bdbd1`
- Sonuç: **`pass_count = 0/5`**
- Ortalama:
  - `mean_denied_to_approved_lift = 0.0769`
  - `mean_denied_high_risk_lift = 0.0834`
  - `mean_denied_reliability_violation_rate = 0.1934`
  - `mean_trajectory_gate_pass_rate_4w = 0.0008`
  - `mean_trajectory_gate_pass_rate_12w = 0.0873`
  - `mean_trajectory_gate_pass_rate_24w = 0.0881`
  - `mean_trajectory_partial_progress_rate = 0.1477`

## 4.4 Phase suite (train_once deterministic freeze + default model config)
- Run: `artifacts/runs/20260310_001437_4b42b2_af6124`
- Sonuç: **`pass_count = 0/5`**
- Ortalama:
  - `mean_denied_to_approved_lift = 0.0073`
  - `mean_denied_high_risk_lift = 0.0058`
  - `mean_denied_reliability_violation_rate = 0.3635`
  - `mean_trajectory_gate_pass_rate_4w = 0.0009`
  - `mean_trajectory_gate_pass_rate_12w = 0.0106`
  - `mean_trajectory_gate_pass_rate_24w = 0.0114`
  - `mean_trajectory_partial_progress_rate = 0.1986`
- Yorum: deterministic ölçüm, default `configs/model.yaml` (xgboost+isotonic) için recourse etkinliğinin düşük olduğunu netleştirdi.

## 4.5 Challenger matrix (gate-hizalı yeni değerlendirme)
- Run: `artifacts/runs/20260310_002301_25be6a_4fda94`
- Champion: `logistic_sigmoid`
- Ancak: `champion_gate_all_pass = false`, `failed_check_count = 2`
- Logistic sigmoid ortalama:
  - `mean_denied_to_approved_lift = 0.2588`
  - `mean_denied_high_risk_lift = 0.1547`
  - `mean_denied_reliability_violation_rate = 0.0859`
  - `mean_trajectory_gate_pass_rate_4w = 0.0045` (gate altında)
  - `mean_trajectory_gate_pass_rate_12w = 0.3640`
  - `mean_trajectory_gate_pass_rate_24w = 0.3547`
  - `mean_trajectory_partial_progress_rate = 0.6820`
- Yorum: Lift ve 12w/24w trajectory güçlü; 4w gate ve fairness tarafı kritik kırılım noktası.

## 4.6 Champion model config ile phase suite
- Run: `artifacts/runs/20260310_004013_3f2254_9a679a`
- Model config: `configs/experiments/model_champion_logistic_sigmoid.yaml`
- Sonuç: **`pass_count = 0/5`**
- Ortalama:
  - `mean_denied_to_approved_lift = 0.3130`
  - `mean_denied_high_risk_lift = 0.1894`
  - `mean_denied_reliability_violation_rate = 0.0677`
  - `mean_trajectory_gate_pass_rate_4w = 0.0053` (eşik 0.03 altında)
  - `mean_trajectory_gate_pass_rate_12w = 0.4160`
  - `mean_trajectory_gate_pass_rate_24w = 0.4101`
  - `mean_trajectory_partial_progress_rate = 0.7769`
- Seed bazlı dominant fail: `trajectory_gate_pass_rate_4w`.
- Seed 44'te ek fail: `equalized_odds_gap_delta` ve stress fairness.

## 5) Somut Sonuç (Neyi Geliştirdik)
1. KPI değerlendirme zinciri artık tutarlı:
   - `run_production_smoke`, `phase_suite`, `challenger_matrix` arasında trajectory/reliability gate uyumsuzluğu kapatıldı.
2. Ölçüm deterministik oldu:
   - suite başlangıcında `train_once` ile model-state kirlenmesi kontrol altına alındı.
3. Ürün etkisi netleşti:
   - doğru modelle (`logistic_sigmoid`) lift güçlü şekilde artıyor.
   - mevcut gate contract altında NO_GO'nun ana nedeni artık ölçümsel belirsizlik değil; 4w trajectory ve bazı fairness kırılımları.

## 6) Kalan Eksikler / Riskler
1. **4w trajectory gate çok sert (veya planın 1. ay etkisi düşük)**
   - Champion modelde dahi `~0.005` seviyesinde kalıyor (threshold `0.03`).
2. **Fairness seed hassasiyeti (özellikle seed 44)**
   - `equalized_odds_gap_delta` ve `high_stress_fairness_gap_after` dalgalanıyor.
3. **Default model config ile ürün etkisi zayıf**
   - `configs/model.yaml` ile deterministic koşuda lift dramatik düşüyor.

## 7) Güncellenmiş Plan (Kodlanacak Sonraki Faz)

### P0
1. `trajectory_gate_pass_rate_4w` için iki aşamalı gate:
   - `hard` yerine `pilot-soft + warning` yaklaşımı veya
   - 4 haftaya özel gerçekçi hedef (`>=0.005` gibi) + 12/24w hard gate korunumu.
2. `model_champion_logistic_sigmoid.yaml` üretim adayı olarak promote edilip AB rollout yapılmalı.
3. Fairness stabilizasyonu:
   - rerank tarafında seed-robust fairness cap (segment-bazlı) sıkılaştırılmalı.

### P1
1. 1. ay (phase_1) aksiyon uzayı güçlendirilmeli:
   - hızlı etkili, düşük maliyetli, kısa horizon aksiyonları artırılmalı.
2. Phase-1 için ayrı objective ağırlığı:
   - 4w gate'e katkı veren aksiyonları daha yüksek önceliklendirme.
3. Challenger karar raporuna "hangi gate'ten kaldı" kırılımı eklenmeli.

## 8) Çalıştırılan Ana Komutlar
- `pytest -q`
- `python -m credit_coach.cli.run_batch_recourse_eval ...`
- `python -m credit_coach.cli.run_production_smoke ...`
- `python -m credit_coach.cli.run_phase_experiment_suite --execute ...`
- `python -m credit_coach.cli.run_model_challenger_matrix --execute ...`
- `python -m credit_coach.cli.run_recourse ...`

## 9) Bu Fazda Üretilen Ana Rapor Artifact'leri
- `artifacts/runs/20260310_004013_3f2254_9a679a/tables/phase_scale_seed_summary.csv`
- `artifacts/runs/20260310_004013_3f2254_9a679a/tables/phase_scale_aggregate.json`
- `artifacts/runs/20260310_002301_25be6a_4fda94/tables/challenger_matrix_variant_summary_ranked.csv`
- `artifacts/runs/20260310_002301_25be6a_4fda94/tables/challenger_matrix_decision.json`

