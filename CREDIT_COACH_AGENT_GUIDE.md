# CREDIT‑COACH  
## Bitirme Tezi + Startup Ürünü için Uçtan Uca Agent Rehberi (Tek Kaynak Doküman)

Bu doküman, bugüne kadar konuştuğumuz **tüm fikirleri**, **geliştirmeleri**, **matematiksel formülasyonları**, **mimariyi**, **dosya yapısını**, **deneyleri**, **tez planını (12 hafta)** ve **startup ürünleşme yolunu** tek bir yerde toplar.

Amaç: Bir agent’ın projeyi **kendi inisiyatifine bırakmadan** adım adım uygulayabilmesi.

> **Not (hukuki):** Basel/BDDK/SR 11‑7/BCBS 239 vb. burada “mühendislik tasarım prensipleri” olarak ele alınır. Bu doküman **hukuki görüş değildir**.

---

## 0) Büyük Resim

Bu proje iki katmandan oluşur:

1) **Research Core (Tez/Makale çekirdeği)**  
   - Risk modeli (XGBoost) + calibration  
   - SHAP açıklamalar  
   - Recourse üretimi (3/6/12 ay × 3 strateji)  
   - **ReX ile nedensel kısıt/ceza**  
   - **Bootstrap CI Upper‑Bound Acceptance** ile istatistiksel güvenlik  
   - Makro stres + şok senaryoları + plan **reliability**  
   - Benchmark (DiCE) + Fairness analizi  
   - Drift/monitoring + Champion‑Challenger governance

2) **Product Layer (Startup ürünü)**  
   - Policy engine (banka kuralları / risk appetite)  
   - Behaviour/feasibility modeli (aksiyon yapılabilir mi?)  
   - Portfolio impact (bankaya toplam risk etkisi)  
   - API + Dashboard + Audit + Monitoring + Data lineage  
   - Haftalık coaching loop (dinamik takip, replan)

Bu iki katman **aynı kod tabanı** üzerinde ilerler.

---

## 1) Veri Stratejisi (Çok Kritik)

### 1.1 LendingClub kullanım politikası
- **Model eğitimi ve akademik deneyler**: LendingClub **dosyadan** (CSV/Parquet) kullanılır.  
- **DB**: LendingClub ham satırlarını depolamak için değil; **ürün state’i** için kullanılır:
  - customer snapshots (x_t)
  - macro snapshots (z_t) + events
  - plan history + plan reviews + overrides
  - model runs + metrics + audit trail

> Bu ayrım bitirme süresini şişirmeden “ürünleşebilir” mimari sağlar.

### 1.2 48 Feature Lock (Zorunlu)
Model input **tam olarak** 48 kolondur. Liste tek kaynaktan yönetilir:

- `configs/features_48.yaml`

**Fail‑fast kuralı:**  
`data/ingest.py` şu kontrolleri yapmak zorunda:
- Listedeki 48 kolonun hepsi veride yoksa → **hard fail**
- Veri ekstra kolon içeriyorsa → yalnızca 48’ini al, diğerlerini drop et
- Pipeline’ın hiçbir yerinde (train/predict/SHAP/recourse) bu liste dışına çıkılamaz.

> ⚠️ Kullanıcı “48 kolon listesi”ni `configs/features_48.yaml` içine **aynen** yapıştırmadan agent devam etmemeli.

---

## 2) Teknoloji Yığını (Sabit)

### Tez + MVP
- Python 3.11
- numpy, pandas
- scikit‑learn
- xgboost
- shap
- dice‑ml (baseline)
- matplotlib (seaborn kullanma)
- pydantic
- pyyaml
- sqlalchemy + sqlite (MVP)
- apscheduler (weekly jobs)
- streamlit
- pytest
- joblib

### Ürün fazı ekleri (tezden sonra)
- FastAPI
- PostgreSQL
- Redis + Celery/RQ
- Docker
- MLflow (opsiyonel)
- Evidently / Alibi‑Detect (drift gözlemi)

---

## 3) Repo Yapısı (Agent değiştirmeyecek)

```text
credit-coach/
  README.md
  pyproject.toml
  requirements.txt
  .env.example

  configs/
    default.yaml
    features_48.yaml          # <-- 48 kolon kilidi (zorunlu)
    model.yaml
    recourse.yaml
    causality.yaml
    safety.yaml
    macro.yaml
    coaching.yaml
    retraining.yaml
    governance.yaml           # risk appetite + gate eşikleri

  data/
    raw/                      # LendingClub ham (commit edilmez)
    processed/                # 48 kolonlu parquet
    splits/                   # train/test indexleri
    demo/                     # offline demo senaryosu verisi

  artifacts/
    models/
    explainers/
    reports/
    runs/
      <run_id>/
        config_snapshot.yaml
        metrics.json
        tables/
        figures/
        logs.txt

  src/credit_coach/
    __init__.py

    utils/
      run_context.py          # run_id + artifact yönetimi
      hashing.py              # dataset hash / config hash

    data/
      ingest.py               # 48-feature lock enforcement burada
      preprocess.py
      features.py
      split.py
      schema.py               # Pydantic şemalar

    storage/                  # ürün state store
      db.py
      models.py
      repository.py

    model/
      train.py
      evaluate.py
      calibrate.py
      predict.py
      registry.py

    xai/
      shap_global.py
      shap_local.py

    causality/
      rex_runner.py           # ReX/alternatif causal discovery runner
      graph_utils.py          # DAG queries
      action_constraints.py   # graph -> penalty/constraints

    recourse/
      action_space.py         # actionable bounds/steps/directions/cost/time
      generator.py            # beam search + causal penalty
      region_targets.py       # point -> interval output
      dice_baseline.py        # baseline

    safety/
      feasibility.py          # hard feasibility gate
      statistical.py          # bootstrap CI upper-bound acceptance
      validator.py            # mapping + reasons

    macro/
      sources.py              # macro snapshot loader (CSV/mock now, API later)
      stress_index.py         # macro_stress_index compute
      events.py               # event registry
      impact.py               # event -> threshold shift + alpha tightening
      shock_scenarios.py
      reliability.py
      shock_sim.py
      drift_detect.py         # PSI

    coaching/
      planner.py              # 3/6/12 horizon plan policy
      progress.py             # improving/stagnant/deteriorating
      reviewer.py             # plan validity+reliability under current macro
      loop.py                 # weekly orchestrator
      messaging.py            # progressive disclosure reason codes

    evaluation/
      metrics.py              # validity/proximity/sparsity/cost/safe-rate + risk_margin
      bootstrap.py            # CI helpers
      fairness.py
      tables.py
      plots.py

    retraining/
      scheduler.py
      data_window.py
      train_job.py
      model_selection.py
      governance.py           # champion-challenger gate + rollback

    policy/
      engine.py               # (startup phase) policy rules (hard/soft)
      rules.yaml              # (startup phase) configurable rules

    portfolio/
      impact.py               # (startup phase) portfolio PD reduction estimates

    app/
      streamlit_app.py
      components.py
      state.py

    api/                      # (startup phase)
      main.py                 # FastAPI
      schemas.py
      auth.py

    cli/
      run_prepare_data.py
      run_train.py
      run_recourse.py
      run_shock.py
      run_benchmark.py
      run_fairness.py
      run_coaching.py
      run_retrain.py
      run_governance_report.py

  tests/
    test_feature_lock.py
    test_action_space.py
    test_rex_constraints.py
    test_validator_ci.py
    test_metrics.py
    test_coaching_progress.py
```

---

## 4) Konfigürasyonlar (Zorunlu alanlar)

### 4.1 `configs/features_48.yaml`
```yaml
features:
  - <COL_1>
  - <COL_2>
  # ...
  - <COL_48>

target:
  name: <TARGET_COL>          # ör: loan_status_binary
  positive_label: 1

id_columns:
  - <OPTIONAL_ID_COL>         # yoksa boş bırakılabilir

time_column: <OPTIONAL_TIME_COL>  # yoksa null

rules:
  fail_on_missing: true
  drop_extra_columns: true
```

### 4.2 `configs/model.yaml`
- XGBoost params
- calibration method
- decision threshold `tau_0`

### 4.3 `configs/recourse.yaml`
- horizons `[3,6,12]`
- strategies `{conservative, balanced, aggressive}`
- topk shap features
- beam width, max actions

### 4.4 `configs/causality.yaml`
- ReX params (veya fallback algorithm)
- penalty weight `w_causal`
- graph output path `artifacts/models/causal_graph.json`

### 4.5 `configs/safety.yaml`
- bootstrap B
- base alpha (0.05)
- high stress alpha (0.01)
- acceptance mapping

### 4.6 `configs/macro.yaml`
- macro feature list
- stress_index weights
- event impact mapping
- shock scenarios list

### 4.7 `configs/retraining.yaml`
- cadence (weekly/monthly)
- rolling window
- champion‑challenger thresholds

### 4.8 `configs/governance.yaml`
- risk appetite + gates:
  - min_auc_drop
  - max_ece
  - max_fairness_gap
  - min_avg_risk_margin
  - min_reliability
  - psi_trigger

---

## 5) Matematiksel Formülasyon (Tez Bölümü için)

### 5.1 Risk modeli ve karar
\[
f(x, z_t) = P(Y=1 \mid x, z_t)
\]
Karar:
\[
\text{approve}(x) \iff f(x,z_t) \le \tau_t
\]

### 5.2 Recourse (kısıtlı optimizasyon)
Verilen reddedilmiş müşteri \(x\), hedef \(x'\):
\[
\min_{x'} C(x,x')
\]
Öyle ki:
\[
f(x', z_t) \le \tau_t
\]
\[
x' \in \mathcal{A} \quad (\text{actionable set})
\]
\[
x' \in \mathcal{F} \quad (\text{feasible set: bounds/direction/domain})
\]

Örnek maliyet:
\[
C(x,x')=\lambda_1\|x'-x\|_1+\lambda_2\,Time(x,x')+\lambda_3\,Cost(x,x')
\]

### 5.3 ReX ile nedensel tutarlılık (kısıt / ceza)
ReX’ten DAG \(G\) elde edilir. Planın aksiyon seti \(A\) için nedensel ceza:
\[
CausalPenalty(A;G)
\]
Plan skoru:
\[
Score = w_1(\tau_t - U_{1-\alpha}(p(x'))) + w_2 R(x') - w_3 C(x,x') - w_4 CausalPenalty(A;G)
\]

> Amaç: korelasyonel “yanıltıcı” aksiyonları azaltmak; parent‑child ilişkilerle tutarlı planları öne almak.

### 5.4 İstatistiksel güvenlik: Bootstrap CI Upper‑Bound Acceptance
Bir planın modeli “geçti” demesi için tek tahmin yetmez. Bootstrap ile:
\[
p_b(x') = f_b(x', z_t), \quad b=1..B
\]
Percentile CI:
\[
CI_{low}=Q_{\alpha/2}(p_b),\quad CI_{high}=Q_{1-\alpha/2}(p_b)
\]
**Kabul kuralı:**
\[
CI_{high} \le \tau_t
\]
Yorum:
> “En kötü ihtimalle bile planın riski eşik altında.”

### 5.5 Dinamik alpha (makro‑duyarlı güven seviyesi)
Makro stres indeksi \(MSI_t \in [0,1]\):
\[
\alpha(z_t)=
\begin{cases}
0.05 & MSI_t \le 0.7 \\
0.01 & MSI_t > 0.7
\end{cases}
\]

### 5.6 Makro şok altında güvenilirlik (Reliability)
Senaryolar \(S=\{s_1,\dots,s_K\}\) (faiz+2, faiz+5, threshold shift vb.):
\[
I_s=
\begin{cases}
1 & f(x',z_t^{(s)}) \le \tau_t^{(s)}\\
0 & \text{otherwise}
\end{cases}
\]
\[
R(x')=\frac{1}{K}\sum_{s=1}^K I_s
\]

### 5.7 Çok ufuklu planlama
\[
H=\{3,6,12\}
\]
Her \(h\in H\) için plan seti üretilir ve skorlanır.

### 5.8 Haftalık coaching (sequential recourse)
Durum:
\[
s_t=(x_t,z_t)
\]
İlerleme:
\[
\Delta p_t = f(x_t,z_t) - f(x_{t-1},z_{t-1})
\]
Eğer \(\Delta p_t\) kötüleşirse veya \(CI_{high}>\tau_t\) olursa → **replan**.

---

## 6) Algoritmalar ve Uygulama Kuralları

### 6.1 Data prep (fail‑fast)
1) raw LendingClub yükle  
2) 48 feature + target seç  
3) preprocess + encode  
4) train/test split  
5) `data/processed/*.parquet` yaz  

### 6.2 Model train + calibration
- XGBoost train
- calibration (Isotonic/Platt)
- metrics: AUC, F1, PR‑AUC, Brier/ECE
- model registry: `model_version`

### 6.3 SHAP
- global importance
- local explanation (top‑k)

### 6.4 ReX (causal discovery)
- ReX runner: datasetten causal graph üret
- graph utils: parent/child queries
- action_constraints: plan aksiyonlarına causal penalty uygula

**MVP notu:** ReX kütüphanesi yoksa, interface korunarak “causal‑learn PC/NOTEARS” gibi bir algoritmayla DAG çıkar; fakat dosya ve API ismi ReX olarak kalır (tezde “ReX adapter”).

### 6.5 Recourse generator (beam search)
- aday feature listesi: local SHAP top‑k ∩ actionable
- beam search ile candidate plans
- planlar 3 strateji × 3 horizon

### 6.6 Safety validation (2 aşama)
**(A) Feasibility Gate**
- actionable, bounds, direction, step
- infeasible → REJECTED

**(B) Statistical Safety Gate**
- bootstrap CI hesapla
- \(CI_{high} \le \tau_t\) → APPROVED  
- değilse → NEEDS_REVIEW (veya CONDITIONAL)

### 6.7 Macro module
- macro sources: CSV/mock now
- stress index compute
- event impact: threshold shift + alpha tightening
- shock scenarios + reliability

### 6.8 Evaluation
- Our vs DiCE: validity/proximity/sparsity/cost/safe‑rate
- Bootstrap CI raporu: approval_rate, avg_risk_margin
- Fairness: group cost gap + approval gap

### 6.9 Drift + Retrain (governance)
Model yenilenince karşılaşılabilecek durumlar:
- covariate shift (drift)
- concept drift
- label delay
- feedback loop / selection bias
- calibration & fairness regressions

Aksiyonlar:
- drift tespit (PSI) → retrain adayı
- calibration bozuldu → **recalibrate**
- fairness gap artışı → deploy yok
- recourse acceptance düşüşü → deploy yok / rollback
- champion‑challenger compare → PASS/FAIL

### 6.10 Regülasyon‑benzeri tasarım prensipleri (tezde “aligned” olarak yaz)
- Model inventory + versioning (SR 11‑7 / MRM yaklaşımı)
- Data lineage + audit (BCBS 239 ruhu)
- Stress testing (Basel/BDDK yaklaşımı)
- Fairness & transparency (fair lending / explainability)

---

## 7) Çıktı Standartları (Artifacts + Audit)

### 7.1 Run klasörü zorunlu içerik
- `config_snapshot.yaml`
- `metrics.json`
- `tables/*.csv`
- `figures/*.png`
- `logs.txt`

### 7.2 Tez için minimum grafik seti
- ROC + calibration curve
- SHAP global bar
- CI distribution / risk_margin histogram
- acceptance frontier (risk_margin vs cost)
- reliability histogram
- fairness cost boxplot
- benchmark tablosu grafiği
- coaching trend grafikleri

---

## 8) CLI Komutları (Agent bunları sağlamalı)

- `run_prepare_data.py`  
  raw → processed (48‑feature locked)

- `run_train.py`  
  model train + calibrate + evaluate

- `run_recourse.py`  
  tek müşteri için 9 plan üret + validate + reliability + save

- `run_shock.py`  
  macro shock reliability batch

- `run_benchmark.py`  
  Our vs DiCE

- `run_fairness.py`  
  fairness eval

- `run_coaching.py`  
  weekly loop (weeks=4 demo)

- `run_retrain.py`  
  challenger train + compare + governance decision

- `run_governance_report.py`  
  PASS/FAIL raporu

---

# PART A — TEZ SÜRECİ (12 HAFTALIK PLAN)

## Genel hedef
12. hafta sonunda:
- offline demo (Streamlit)
- tez için tüm tablolar/figürler
- benchmark + fairness + macro shock + coaching loop
- ReX entegrasyonu
- Bootstrap CI safety validator çalışır

---

## HAFTA 1 — Proje iskeleti + config + feature lock + schema + DB
**Deliverable**
- Repo yapısı kurulu
- `features_48.yaml` (placeholder + fail‑fast)
- Pydantic şemalar
- SQLite state store

**Kapatılacak işler**
- `utils/run_context.py`
- `data/schema.py`
- `storage/models.py` + `repository.py`
- `test_feature_lock.py` (en az fail‑fast)

**Komut**
- `python -m credit_coach.cli.run_train --dry_run`
- `pytest`

---

## HAFTA 2 — LendingClub ingest + preprocess + 48 feature parquet
**Deliverable**
- `data/processed/train.parquet` ve `test.parquet` (48 feature + target)
- data summary tablosu

**Kapatılacak işler**
- `data/ingest.py` (fail‑fast)
- `data/preprocess.py`, `data/features.py`, `data/split.py`
- `cli/run_prepare_data.py`

**Komut**
- `python -m credit_coach.cli.run_prepare_data --config configs/default.yaml`

---

## HAFTA 3 — Model train/evaluate + calibration + registry
**Deliverable**
- trained model + calibrator
- ROC + calibration curve

**Kapatılacak işler**
- `model/train.py`, `evaluate.py`, `calibrate.py`, `predict.py`, `registry.py`

**Komut**
- `python -m credit_coach.cli.run_train --config configs/model.yaml`

---

## HAFTA 4 — SHAP global/local + explanation outputs
**Deliverable**
- SHAP global top‑20 + figür
- tek müşteri local top‑k reasons

**Kapatılacak işler**
- `xai/shap_global.py`, `xai/shap_local.py`

**Komut**
- `python -m credit_coach.cli.run_recourse --customer_id demo --explain_only`

---

## HAFTA 5 — ReX (causal graph) + action constraints + action space
**Deliverable**
- `causal_graph.json`
- causal penalty hesapları
- action_space tanımı

**Kapatılacak işler**
- `causality/rex_runner.py` (graph export)
- `causality/graph_utils.py`
- `causality/action_constraints.py`
- `recourse/action_space.py`
- `tests/test_rex_constraints.py`

---

## HAFTA 6 — Recourse generator (beam search) + 9 plan üretimi
**Deliverable**
- 9 plan JSON/CSV
- region‑based target opsiyonu

**Kapatılacak işler**
- `recourse/generator.py`
- `coaching/planner.py`
- `recourse/region_targets.py`

**Komut**
- `python -m credit_coach.cli.run_recourse --customer_id demo`

---

## HAFTA 7 — Statistical safety (Bootstrap CI) + feasibility gate
**Deliverable**
- her plan için CI_low, CI_high, upper_bound, risk_margin, alpha_used
- status mapping (APPROVED/NEEDS_REVIEW/REJECTED)

**Kapatılacak işler**
- `safety/feasibility.py`
- `safety/statistical.py`
- `safety/validator.py`
- `tests/test_validator_ci.py`

---

## HAFTA 8 — Macro stress index + events + shock reliability
**Deliverable**
- macro_stress_index
- dynamic alpha(z_t)
- shock scenarios + reliability

**Kapatılacak işler**
- `macro/stress_index.py`
- `macro/events.py`, `impact.py`
- `macro/shock_scenarios.py`, `reliability.py`, `shock_sim.py`
- `cli/run_shock.py`

---

## HAFTA 9 — Benchmark (DiCE) + Evaluation + Fairness
**Deliverable**
- Our vs DiCE tablo
- fairness group tablo + figür
- acceptance frontier figürü

**Kapatılacak işler**
- `recourse/dice_baseline.py`
- `evaluation/metrics.py`, `bootstrap.py`, `fairness.py`, `tables.py`, `plots.py`
- `cli/run_benchmark.py`, `cli/run_fairness.py`

---

## HAFTA 10 — Weekly coaching loop + demo senaryosu (4 hafta)
**Deliverable**
- 4 haftalık run: progress labels + replan event
- plan review raporu

**Kapatılacak işler**
- `coaching/progress.py`, `reviewer.py`, `loop.py`, `messaging.py`
- `cli/run_coaching.py`
- `data/demo/` offline senaryo (week3 macro shock)

---

## HAFTA 11 — Retraining governance + monitoring + Streamlit UI
**Deliverable**
- champion‑challenger compare (PASS/FAIL)
- governance report
- Streamlit 4 ekran

**Kapatılacak işler**
- `macro/drift_detect.py` (PSI)
- `retraining/*`
- `cli/run_retrain.py`, `cli/run_governance_report.py`
- `app/streamlit_app.py`

---

## HAFTA 12 — Final Thesis Pack + Freeze + Sunum hazırlığı
**Deliverable**
- 1000+ sample batch run çıktıları
- tüm tablo/figür paketlenmiş
- offline demo stabil

**Kapatılacak işler**
- “final_thesis_pack” rapor klasörü
- README: demo çalıştırma adımları
- tam smoke test + pytest

---

# PART B — STARTUP SÜRECİ (Tez Sonrası Ürünleşme Yol Haritası)

Bu bölüm “tez bittiğinde” başlayacak şekilde planlanmıştır. Çekirdek motor korunur; ürün katmanı eklenir.

## B1) MVP Ürün Tanımı (satılabilir ilk sürüm)
**Tek cümle değer önerisi:**  
“Kredi alamayan müşteriye, bankanın risk iştahına ve makro koşullara göre güncellenen, güven aralıklı (CI) ve nedensel tutarlı iyileştirme planı sunan koçluk sistemi.”

### İlk müşteri segmenti seçimi
- B2B (bankaya/fintech’e dashboard + API) önerilir (daha hızlı gelir)
- B2C (son kullanıcı koçluğu) daha çok kullanıcı edinimi gerektirir

## B2) Ürün mimarisi (servisleşme)
- FastAPI: `/score`, `/plans`, `/weekly/review`, `/events`
- PostgreSQL: snapshots, plans, audits
- Redis+Queue: batch coaching + monitoring
- Auth: role‑based (analyst vs customer)

## B3) Product‑critical modüller (tezde yoksa ekle)
### (1) Policy Engine (hard rules)
- min income, max DTI, fraud flags, blacklists, risk appetite rules
- `policy/engine.py` + YAML rules

### (2) Behaviour / Feasibility Model
- her action için “yapılabilirlik olasılığı”
- plan skoruna `expected_compliance` eklenir

### (3) Portfolio Impact Layer
- 1000+ müşteri için PD reduction
- bankaya “expected loss improvement” raporu

### (4) Compliance & UX
- “garanti değildir” uyarısı
- progressive disclosure
- audit log immutable

## B4) Operasyon & Güvenlik (MVP‑prod arası)
- logging (structured)
- monitoring (drift + calibration + fairness + recourse KPIs)
- rollback planı
- secrets management

---

## 9) Agent “Düşünme Biçimi” Kuralları (Çok önemli)

1) **Fail‑fast**: Feature lock bozulursa hiçbir şey koşma.  
2) **Config‑first**: Kodda hard‑code yok; her şey YAML’den.  
3) **Traceability**: Her çıktı run_id ile izlenebilir olmalı.  
4) **Separation of concerns**: Training data (files) ≠ product state (DB).  
5) **Academic validity**: Her iddia bir metrik/tabloda görünmeli (CI, benchmark, fairness, reliability).  
6) **Scope discipline**: NLP haber analizi / RL policy learning / microservice deploy tez döneminde yok.  
7) **Single source of truth**: 48 features listesi tek dosyada.  
8) **Status determinism**: Plan status sadece feasibility + CI upper‑bound acceptance ile belirlenir (net ve savunulabilir).

---

## 10) “Done” Tanımı (Kısa)
Tez dönemi sonunda sistem şunları yapabiliyorsa tamam:
- LendingClub 48 feature ile model eğit
- SHAP üret
- 9 plan üret (3/6/12 × 3)
- ReX causal penalty uygula
- Bootstrap CI upper‑bound acceptance ile status ver
- Macro shock reliability hesapla
- DiCE benchmark + fairness raporu üret
- Weekly coaching loop demo (4 hafta) + replan göster
- Streamlit offline demo çalıştır
- Retrain governance PASS/FAIL raporu üret

---

## Ek: Kullanıcıdan Gereken Tek Kritik Girdi
- **48 kolon listesi** + target adı → `configs/features_48.yaml`  
Agent bu olmadan ilerlememeli.

