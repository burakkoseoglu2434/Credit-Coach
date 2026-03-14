# CREDIT COACH FINTECH HARDENING - SPRINT 4 RAPORU

## 0) Kapsam
Sprint: `Sprint-4 (Hafta 7-8)`  
Backlog maddesi: `C2 - Sequential recourse planner`  
Tarih: `2026-03-07`

Hedef:
1. Haftalik multi-step state transition modeli eklemek.
2. Action dropout/noise ile execution gercekligini simule etmek.
3. Dinamik review/replan mekanizmasini haftalik karar dongusune baglamak.

---

## 1) Yapilan Degisiklikler (Dosya Bazli)

### 1.1 Sequential coaching loop
- `credit-coach/src/credit_coach/coaching/loop.py`
  - Fonksiyon yeniden tasarlandi: `run_weekly_coaching_loop(...)`
  - Yeni yetenekler:
    1. Multi-step PD state transition
    2. Haftalik action planlama (`planned_actions`)
    3. Action dropout modeli (`missed_action`)
    4. Execution noise modeli (`execution_noise_std`)
    5. Makro sok schedule destegi
    6. Dinamik target PD adaptasyonu
    7. Robust margin hesaplama
  - Yeni cikti kolonlari:
    - `planned_actions`, `executed_actions`, `remaining_actions`
    - `missed_action`, `missed_actions_streak`, `execution_rate`
    - `shock_delta`, `target_pd`, `robust_margin`
    - `replan_reasons`, `reason_codes`

### 1.2 Dinamik replan reviewer
- `credit-coach/src/credit_coach/coaching/reviewer.py`
  - Yeni fonksiyon: `evaluate_replan(...) -> (bool, reasons)`
  - Replan trigger nedenleri:
    1. `deteriorating_progress`
    2. `ci_exceeds_tau`
    3. `missed_actions_streak`
    4. `robust_margin_below_gate`
  - `needs_replan(...)` backward-compatible bool wrapper olarak korundu.

### 1.3 Messaging ve planner iyilestirme
- `credit-coach/src/credit_coach/coaching/messaging.py`
  - `reason_codes(...)` artık opsiyonel `replan_reasons` aliyor.

- `credit-coach/src/credit_coach/coaching/planner.py`
  - Best plan seciminde `robust_score` oncelemesi eklendi.

### 1.4 Coaching CLI entegrasyonu
- `credit-coach/src/credit_coach/cli/run_coaching.py`
  - En iyi plan secimi robust-aware hale getirildi.
  - `coaching.yaml` altindaki yeni `sequential` ve `robust_gates` ayarlari loop’a aktariliyor.
  - Opsiyonel `macro_shock_schedule` parse destegi eklendi.
  - Run metrics genisletildi:
    - `target_pd`
    - `achieved_target`
    - `avg_execution_rate`
    - `missed_action_weeks`
    - `selected_plan_id`

### 1.5 Config ve dokumantasyon
- `credit-coach/configs/coaching.yaml`
  - Yeni bloklar:
    - `sequential`
    - `robust_gates`

- `credit-coach/README.md`
  - C2 sequential config ve yeni weekly output kolon notlari eklendi.

- `credit-coach/src/credit_coach/coaching/__init__.py`
  - `evaluate_replan` export edildi.

---

## 2) Test Gelistirmeleri

Yeni test:
- `credit-coach/tests/test_sequential_recourse.py`
  1. Missed actions ile replan tetiklenmesini dogrular.
  2. Robust margin gate ile replan reason dogrular.

Guncellenen test:
- `credit-coach/tests/test_coaching_progress.py`
  - Yeni sequential kolonlarin varligini dogrular.

---

## 3) Calistirilan Komutlar ve Sonuclar

1. Hedefli testler:
```bash
cd credit-coach && pytest -q tests/test_coaching_progress.py tests/test_sequential_recourse.py tests/test_robust_recourse.py tests/test_validator_ci.py
```
Sonuc: `7 passed`

2. Tam regresyon:
```bash
cd credit-coach && pytest -q
```
Sonuc: `62 passed, 9 warnings`

3. Uctan uca coaching run:
```bash
cd credit-coach && python -m credit_coach.cli.run_coaching --weeks 6 --coaching_config configs/coaching.yaml --model_config configs/model.yaml
```
Run ID: `20260307_005945_620052_d4c66d`  
Cikti: `artifacts/runs/20260307_005945_620052_d4c66d/tables/weekly_coaching.csv`

Run metrics:
1. `weeks: 6`
2. `replan_count: 0`
3. `final_pd: 0.0`
4. `target_pd: 0.0234`
5. `achieved_target: true`
6. `avg_execution_rate: 0.6667`
7. `missed_action_weeks: 2`

Not:
- Bu run’da secilen plan guclu oldugu icin replan tetiklenmedi.
- Replan tetiklenme davranisi `test_sequential_recourse.py` icinde dropout=1.0 senaryosunda dogrulandi.

---

## 4) Backlog Durumu
Sprint-4 backlog:
1. `C2 - Sequential recourse planner`: Tamamlandi (kod + test + run output)

Sprint gate:
1. Multi-step transition aktif.
2. Dynamic replan trigger mekanizmasi aktif.
3. Test seti yesil (`62 passed`).

---

## 5) Acilan Riskler ve Teknik Borc
1. Synthetic transition modeli su an lineer/heuristic; ileride customer-level behavior model ile kalibre edilmeli.
2. `datetime.utcnow()` deprecation warningleri devam ediyor.
3. DiCE runtime fallback (`heuristic_fallback_error`) devam ediyor; ortam/wrapper sertlestirmesi gerekiyor.

---

## 6) Sonraki Sprint Giris Kosullari (Sprint-5)
1. C2 tamamlandi.
2. Sonraki odak: `D1 + D2` (rolling window backtesting + fairness stress matrix).

