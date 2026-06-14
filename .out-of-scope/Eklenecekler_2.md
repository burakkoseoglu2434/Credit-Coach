13.04.2026

⸻

🚀 Milestone: Phase 71 — Performance & Scalability Optimization

🎯 Objective
	•	run_v24_cohort_evaluation pipeline’ını:
	•	≥5–10x hızlandırmak
	•	3000 → 100k scale’e hazırlamak
	•	çıktı kalitesini korumak (trust-clean + metric parity)

⸻

📦 Scope (2 kategori)

🟢 Track A — Quality-Neutral Optimizations (MUST DO)

Davranışı değiştirmez, sadece hızlandırır.

A1. Fairness Penalty Caching
	•	group_penalties computation’ı customer loop dışına al
	•	tek sefer compute + global reuse
	•	verify: aynı output mu?

📈 Expected impact:
	•	2–5x hız kazanımı

⸻

A2. Batch Model Inference (Weekly Optimizer)
	•	_pd_for_candidate() yerine:
	•	feature candidates → tek DataFrame
	•	tek predict_proba call
	•	loop → vectorized

📈 Expected impact:
	•	3–10x speedup (optimizer kısmında)

⸻

A3. SHAP Optimization
	•	background sample → run başında compute
	•	explainer reuse
	•	optional flag:
	•	--disable_shap_for_large_runs

📈 Expected impact:
	•	1.5–3x hız

⸻

A4. Artifact Slimming
	•	candidate_plans.jsonl → “thin schema” mode
	•	full JSON sadece:
	•	selected plans
	•	debug sample (%1)

📈 Expected impact:
	•	disk + memory + serialization iyileşmesi

⸻

🟡 Track B — Structural Improvements (HIGH IMPACT)

B1. Internal Planner Deadline Enforcement
	•	deadline_ts → cohort pipeline’a geçir
	•	per_customer_time_budget_ms → gerçek enforce

📈 Impact:
	•	worst-case runtime kontrol altına alınır

⸻

B2. SHAP Optional Mode
	•	config:
	•	shap_mode: full | minimal | off
	•	large runs → default minimal

⸻

B3. Two-Pass Strategy (Optional)
	•	Pass 1: cheap heuristic
	•	Pass 2: full search (subset)

📈 Impact:
	•	100k+ scale için kritik

⸻

B4. Parallelization (v1)
	•	multiprocessing (customer-level)
	•	chunk-based execution

📈 Impact:
	•	linear speedup (CPU core kadar)

⸻

🧪 Validation Plan (CRITICAL)

Golden Set
	•	n=300 (seed 42 & 43)
	•	baseline vs optimized karşılaştır

Checkpoints
	•	cohort_metrics.json identical / near-identical
	•	trust_summary.json identical
	•	decision (ADMISSIBLE vs NOT) değişmiyor

Tolerance
	•	minor numeric drift OK
	•	structural difference ❌ NOT OK

⸻

📊 Success Metrics

Metric	Target
Runtime (n=3000)	↓ 5–10x
Memory usage	↓
Artifact size	↓ 50–90%
Trust metrics	unchanged
Final decision	unchanged


⸻

🧭 Execution Plan (Order)

Step 1 (1–2 gün)
	•	A1: fairness cache
	•	A3: SHAP reuse

👉 hızlı win

⸻

Step 2 (2–3 gün)
	•	A2: batch inference

👉 en büyük performans sıçraması

⸻

Step 3 (1 gün)
	•	A4: artifact slimming

⸻

Step 4 (2–4 gün)
	•	B1: deadline enforcement
	•	B2: shap modes

⸻

Step 5 (opsiyonel ama önemli)
	•	B4: parallelization

⸻

⚠️ Risk Management

Yapma:
	•	❌ candidate sayısını düşürme (şimdilik)
	•	❌ pruning ekleme
	•	❌ heuristic ile search’i kısma

Neden:

→ Phase 70 goal: behavior preserve etmek

⸻

🧠 Final Outcome

Bu milestone sonunda:
	•	3000 → saatler değil, dakikalar
	•	10k → pratik hale gelir
	•	100k → yapılabilir olur
	•	1M → gerçekçi plan yapılabilir

⸻

🎯 Tek cümlelik özet

Phase 71 = “aynı algoritmayı daha akıllı çalıştırarak scale’e hazır hale getirmek”

⸻

İstersen bunu Jira / Notion ticket’larına bölüp task breakdown da çıkarabilirim 👍