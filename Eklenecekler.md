Aşağıda, şimdiye kadar konuştuğumuz tüm eksikler ve geliştirme ihtiyaçlarını birleştirerek hem model/engine tarafı hem de web/product tarafı için bütünlüklü bir roadmap çıkardım.

Bunu şu mantıkla kurdum:
	•	önce motorun gerçekten güçlü ve güvenilir olması
	•	sonra önerilerin gerçek dünyaya yaklaşması
	•	sonra offer/policy/learning loop
	•	sonra ürünleşme ve web yüzeyi
	•	en sonda operasyonel ve ticari olgunluk

Bu planı istersen daha sonra doğrudan .planning/ROADMAP.md veya GSD faz dosyalarına da çevirebiliriz.

⸻

Genel strateji

Ana gerçek

Bugün elindeki sistem:
	•	güçlü bir credit decisioning + recourse engine
	•	iyi bir fairness / KPI / governance altyapısı
	•	iyi bir trajectory / offer / evidence yönü

Ama henüz:
	•	tam davranış-gerçekçi
	•	tam öğrenen
	•	tam ürünleşmiş
	•	tam kurumsal web yüzeyine oturmuş

değil.

Bu yüzden roadmap iki ana hatta ayrılmalı:

Hat A — Model / Engine

Karar motorunu daha gerçekçi, davranışa duyarlı, ticari ve öğrenebilir hale getirmek.

Hat B — Web / Product Surface

Bu motoru yatırımcıya, kurum alıcısına ve demo kullanıcıya anlaşılır, güven veren ve satılabilir bir ürün yüzeyiyle sunmak.

⸻

Master Roadmap

Milestone M1 — Recommendation Engine Hardening

Amaç: Motorun öneri kalitesini gerçek dünya açısından ciddi şekilde güçlendirmek.

Milestone M2 — Intervention & Offer Intelligence

Amaç: Müşteri aksiyonu + kurum teklifi birlikte optimize edilen finansal müdahale sistemine geçmek.

Milestone M3 — Learning Loop & Policy Intelligence

Amaç: Karar → sonuç → öğrenme döngüsünü kurmak.

Milestone M4 — Productization & Website

Amaç: Tüm bu motoru güçlü bir web uygulaması ve kurumsal ürün hikâyesi ile sunmak.

Milestone M5 — Productionization & Commercial Readiness

Amaç: Gerçek müşteri pilotlarına çıkabilecek seviyeye gelmek.

⸻

M1 — Recommendation Engine Hardening

Bu milestone, konuştuğumuz en kritik eksiklere cevap verir:
	•	feature output hâlâ fazla teknik
	•	aksiyon semantiği eksik
	•	execution reality eksik
	•	kısa / orta / uzun vade dengesi tam oturmamış
	•	demo güçlü ama öneri hala kısmen “engine-native”

⸻

Phase 1 — Action Semantics & Realism Foundation

Amaç

Feature delta’ları gerçek dünya aksiyonlarına çevirebilen sağlam aksiyon semantiğini kurmak.

Neden gerekli

Şu an sistem şuna yakın konuşuyor:
	•	last_fico_range_high 614 -> 671

Ama ürünün konuşması gereken şey:
	•	“3 ay düzenli ödeme göster”
	•	“kredi kartı kullanım oranını düşür”
	•	“yeni gecikme oluşturma”

Yapılacaklar
	1.	Typed action taxonomy’yi finalize et
	•	behavioral
	•	structural
	•	institutional
	2.	Her feature için action mapping dictionary üret
	3.	Bir feature’in hangi gerçek aksiyon veya aksiyon grubuna dönüştüğü netleşsin
	4.	Composite action mantığını stabilize et
	5.	Action serialization standardını netleştir
	•	user-facing action_key
	•	effect anchor feature_name
	•	action_group_id
	6.	Teknik / business görünümü ayrıştır
	•	default görünüm: business action
	•	expanded görünüm: technical effect

Çıktılar
	•	action_catalog
	•	feature_to_action_mapping
	•	gerçek kullanıcı diliyle action templates

Başarı kriterleri
	•	hiçbir ana plan sadece ham feature adıyla sunulmaz
	•	tüm kritik öneriler action semantic’e çevrilebilir
	•	demo ekranındaki planlar insan diliyle okunabilir

⸻

Phase 2 — Feasibility & Constraint Realism

Amaç

Önerilerin gerçek hayatta yapılabilir olmasını sağlamak.

Neden gerekli

Bir öneri matematiksel olarak iyi olabilir ama gerçek hayatta imkânsız olabilir.

Yapılacaklar
	1.	Feasibility kurallarını genişlet
	•	income growth cap
	•	utilization drop bounds
	•	payment capacity
	•	credit-limit realism
	2.	Clip / reject davranışlarını aksiyon sınıfına göre sabitle
	3.	Prerequisite ve conflict katmanını güçlendir
	4.	Repair-if-safe akışını standartlaştır
	5.	Invalid / repaired / provisional plan status’larını tutarlı hale getir
	6.	Approval-dependent institutional action mantığını finalize et

Çıktılar
	•	action_realism_summary.json
	•	feasibility rejection breakdown
	•	repair breakdown

Başarı kriterleri
	•	unrealistic plan’ler ranking’e normal aday gibi giremez
	•	repaired plan’ler izlenebilir
	•	approval pending plan’ler normal winner olmaz

⸻

Phase 19 — Behavior-Aware Recourse

Amaç

Sistemin “müşteri bunu yapar mı?” sorusunu hesaba katması.

Neden gerekli

Bugünkü sistem ağırlıkla:
	•	aksiyon → PD değişimi

ama gerçek dünya:
	•	aksiyon → yapılma olasılığı → PD değişimi

Yapılacaklar
	1.	action_execution_probability contract’ını kur
	2.	plan_execution_probability hesapla
	3.	Composite action’lar için group-level aggregation ekle
	4.	Provisional / approval pending aksiyonları ayrı işle
	5.	Expected utility’yi ranking katmanına ekle
	•	gate değil
	•	ranking/tie-break katmanı
	6.	Execution scenario sınıflarını kur
	•	full_execution
	•	mixed_execution
	•	failed_execution
	7.	Existing weekly loop’u canonical execution seam yap
	8.	Behavior-aware evidence üret

Çıktılar
	•	behavior_aware_summary.json
	•	execution probability breakdown
	•	partial execution breakdown

Başarı kriterleri
	•	ranking yalnız nominal PD improvement’a göre çalışmaz
	•	düşük yapılabilirlikli planlar geriye düşer
	•	behavior-aware metrics suite/challenger’da görünür

⸻

Phase 20 — Sequential / Trajectory Planning

Amaç

Tek aksiyonlu öneriden gerçek faz bazlı yol haritasına geçmek.

Yapılacaklar
	1.	Canonical phases[] yapısını finalize et
	2.	3 fazlı sabit sistem:
	•	phase_1_stabilize
	•	phase_2_build
	•	phase_3_optimize
	3.	Her aksiyonun tek primary phase’i olsun
	4.	Checkpoint semanticlerini sabitle
	•	4w primary
	•	12w confirmation
	•	24w stability/upside
	5.	Soft monotonicity expectation ekle
	6.	Replan mantığını phase boundary seviyesine sabitle
	•	week 4
	•	week 12
	•	week 24
	7.	Trajectory status alanlarını ekle
	•	on_track
	•	needs_replan
	•	degraded
	8.	Policy labels ekle
	•	stabilize_first
	•	balanced_progress
	•	long_horizon_heavy

Çıktılar
	•	trajectory summary artifacts
	•	phased roadmap outputs
	•	checkpoint review structure

Başarı kriterleri
	•	4 haftalık sağlık uzun vadeye kurban gitmez
	•	planlar zaman içinde anlaşılır kalır
	•	replan mantığı kontrollü olur

⸻

M2 — Intervention & Offer Intelligence

Bu milestone şu sıçramayı yapar:

müşteri ne yapmalı
→ müşteri ne yapmalı + kurum ne teklif etmeli

⸻

Phase 21 — Offer Contract & Policy Layer

Amaç

Institutional action’ları gerçek offer engine’e dönüştürmek.

Yapılacaklar
	1.	Institutional actions üstüne offer layer ekle
	2.	offer_type ve offer_terms schema’sını oturt
	3.	Mixed plan içinde tek active offer branch kuralını uygula
	4.	Rankable offer vs provisional offer ayrımını kur
	5.	Offer term completeness kontrolü ekle

Minimum offer schema
	•	offer_type
	•	payment_delta_monthly
	•	discount_amount / discount_pct
	•	term_extension_months
	•	interest_rate_delta
	•	grace_period_weeks
	•	requires_acceptance
	•	requires_institutional_approval

Başarı kriterleri
	•	offer içeren planlar normal ranking’e girebilir
	•	belirsiz institutional placeholders winner olamaz
	•	offer contract engine ile uyumlu olur

⸻

Phase 22 — Recovery Objective & Offer Scoring

Amaç

Teklifleri yalnız risk açısından değil, ticari etki açısından da optimize etmek.

Yapılacaklar
	1.	expected_recovery_proxy objective’ini tanımla
	2.	Canonical business proxies:
	•	approval_rate
	•	default_rate_90d
	•	avg_margin_90d
	3.	Weighted composite optimizer yaz
	4.	Ama review/artifact tarafında metric-by-metric dili koru
	5.	Ranking sırası:
	•	inherited safety gates
	•	feasibility + trajectory health
	•	expected_recovery_proxy
	6.	Governance-safe offer iyileştirme kuralını uygula

Başarı kriterleri
	•	yalnız margin artışıyla kötüleşen planlar “iyi” sayılmaz
	•	recovery proxy iyileşirken fairness / reliability bozulmaz
	•	offer optimization risk stack’i override etmez

⸻

Phase 23 — Offer Acceptance Modeling

Amaç

Plan uygulanabilirliği ile teklif kabulünü ayırmak.

Yapılacaklar
	1.	offer_acceptance_probability ekle
	2.	combined_plan_realization_probability hesapla
	3.	Acceptance estimator input ailesini kur:
	•	offer_type
	•	offer_terms
	•	action_burden
	•	risk_band / income_band / stress_band
	•	short-term trajectory health
	•	approval state
	4.	Policy arm semantiğini offer profilleri için genişlet
	5.	Offer evidence katmanını ekle

Çıktılar
	•	offer_optimization_summary.json
	•	offer type breakdown
	•	offer acceptance breakdown
	•	offer proxy impact breakdown

Başarı kriterleri
	•	plan execution ve offer acceptance birbirine ezilmez
	•	combined realization tutarlı hesaplanır
	•	offer policy arm comparison mümkün hale gelir

⸻

M3 — Learning Loop & Policy Intelligence

Bu milestone sistemin gerçekten “öğrenebilir” hale gelmesini sağlar.

⸻

Phase 24 — Decision Logging Expansion

Amaç

Decision log’u gerçek learning ledger haline getirmek.

Yapılacaklar
	1.	Compact decision logging contract kur
	2.	Full raw plan snapshot’ı log içine gömme
	3.	Stable ids ve summary taşı
	4.	Zorunlu alanlar:
	•	decision_id
	•	plan_id
	•	candidate_set_id
	•	policy_arm
	•	policy_arm_profile
	•	reason_codes
	•	selection_propensity
	5.	Recommendation context summary ekle
	•	selected_plan_status
	•	selected_offer_type
	•	plan_execution_probability
	•	offer_acceptance_probability
	•	combined realization

Başarı kriterleri
	•	decision log audit-safe olur
	•	learning için yeterli context taşır
	•	source-of-truth plan artifact başka yerde kalır

⸻

Phase 25 — Outcome Ingestion & Completeness

Amaç

Gerçek sonuçları normalize etmek ve learning readiness seviyesini ölçmek.

Yapılacaklar
	1.	Outcome ingestion seam’ini genişlet
	2.	Action completion, offer acceptance, payment behavior, recovery outcome ekle
	3.	Completeness status’larını kur
	•	descriptive_only
	•	partial_learning_ready
	•	learning_ready
	4.	Coverage boyutlarını ayrı taşı
	•	has_action_completion
	•	has_offer_acceptance
	•	has_payment_behavior
	•	has_recovery_outcome
	5.	90d’yi primary learning window yap
	6.	Learning readiness summary üret

Çıktılar
	•	decision_logging_summary.json
	•	outcome_ingestion_summary.json

Başarı kriterleri
	•	hangi kayıtların öğrenmeye uygun olduğu açıkça ölçülür
	•	90d coverage görünür olur
	•	sadece descriptive ve learning-ready kayıtlar ayrışır

⸻

Phase 26 — OPE / Learning Evidence

Amaç

Policy comparison’ı descriptive seviyeden OPE seviyesine çıkarmak.

Yapılacaklar
	1.	Canonical IPS ve Doubly Robust modülü yaz
	2.	Reward language’i proxy-vector first tut
	•	approval_rate
	•	default_rate_90d
	•	avg_margin_90d
	3.	Control arm baseline semantics’i sabitle
	4.	Confidence düşüş şartlarını uygula
	•	weak propensities
	•	düşük reward coverage
	•	arm imbalance
	•	düşük effective sample size
	5.	OPE artifact üret
	6.	Review’a Learning Loop Summary ekle

Çıktılar
	•	off_policy_evaluation.json
	•	learning loop review outputs

Başarı kriterleri
	•	OPE descriptive comparison’dan ayrışır
	•	ama non-blocking kalır
	•	learning signals review’da görünür olur

⸻

M4 — Productization & Website

Bu milestone, motoru satılabilir bir web yüzeyine dönüştürür.

⸻

Phase 27 — Website Repositioning

Amaç

Siteyi kurum alıcısı öncelikli, business-first hale getirmek.

Yapılacaklar
	1.	Ana persona = kurum alıcısı
	2.	Hero’a net ürün tanımı ekle
	3.	Home flow:
	•	Problem
	•	Çözüm
	•	Nasıl çalışır
	•	Kanıt
	•	Demo
	•	CTA
	4.	Navbar dili:
	•	Ürün
	•	Nasıl Çalışır
	•	Demo Merkezi
	•	Kanıt
	•	Yatırımcı
	•	İletişim
	5.	TR/EN temiz ayrım
	6.	CTA sistemi tekilleştir

Başarı kriterleri
	•	kullanıcı 5–10 saniyede ürünün ne olduğunu anlar
	•	ana hikâye enterprise buyer’a konuşur
	•	yatırımcı akışı ikinci katmanda korunur

⸻

Phase 28 — Demo Center Refactor

Amaç

Demo merkezi “ham engine output” hissinden çıkıp gerçek ürün yüzeyine dönüşsün.

Yapılacaklar
	1.	Demo merkezi 5 katmana ayrılsın:
	•	overview
	•	tek müşteri
	•	portföy etkisi
	•	teklif optimizasyonu
	•	öğrenme döngüsü
	2.	Her bölümde:
	•	“Bu ekran neden önemli?”
	3.	Tek müşteri ekranında executive summary zorunlu olsun
	4.	Teknik detaylar collapse altında kalsın
	5.	Demo’ya güven etiketi ekle
	•	curated demo snapshot
	•	representative product preview
	6.	KPI’lere bağlam notları ekle

Başarı kriterleri
	•	demo business-first hissi verir
	•	teknik output varsayılan görünümde kullanıcıyı boğmaz
	•	section flow daha anlaşılır olur

⸻

Phase 29 — Proof / Investor Surface

Amaç

Proof ve investor sayfalarını ayrı ama tutarlı şekilde ürünleştirmek.

Yapılacaklar
	1.	Proof sayfası yapısı:
	•	Ne ölçüyoruz
	•	Neden güvenilir
	•	Nasıl release ediyoruz
	•	Nasıl öğreniyoruz
	2.	Governance layer görünür hale gelsin
	3.	Investor sayfasında şunlar net olsun:
	•	neden şimdi
	•	ilk wedge
	•	neden farklı
	•	nasıl para kazanır
	•	kategori
	4.	“Tek platform, çok modül, tek karar yüzeyi” mesajı güçlendirilsin

Başarı kriterleri
	•	yatırımcı ve kurum buyer farklı ama tutarlı mesaj alır
	•	proof, metrik dump değil güven yüzeyi gibi görünür

⸻

Phase 30 — Website Foundation & Full-Stack App Skeleton

Amaç

credit-coach-website uygulamasını sağlam mimariyle kurmak.

Stack
	•	React
	•	Vite
	•	TypeScript
	•	Tailwind
	•	Express
	•	PostgreSQL
	•	Drizzle

Yapılacaklar
	1.	Client / server / shared klasör yapısı
	2.	Typed contracts
	3.	Demo data registry
	4.	Contact/demo-request/investor-request API
	5.	Postgres lead storage
	6.	Artifact-first demo data tüketimi
	7.	Content model temeli
	8.	Responsive core layout

Başarı kriterleri
	•	site static-first ama full-stack hazır olur
	•	backend thin kalır
	•	Python engine source-of-truth olarak korunur

⸻

Phase 31 — Demo Data & Proof Sync

Amaç

Engine artifact’lerinden kontrollü demo / proof snapshot üretmek.

Yapılacaklar
	1.	demo-data/ pipeline kur
	2.	Curated snapshots seç
	3.	Website demo schema’ları yaz
	4.	Sync script yaz
	5.	Demo datayı küçült, temizle, normalize et
	6.	KPI / roadmap / offer / learning artifact’lerini web formatına çevir

Başarı kriterleri
	•	demo’lar stabil çalışır
	•	engine değişse bile website kontrollü kalır
	•	live artifact browse olmadan güçlü proof yüzeyi oluşur

⸻

M5 — Productionization & Commercial Readiness

Bu milestone, hem modelin hem web ürününün pilot seviyesine çıkmasını sağlar.

⸻

Phase 32 — Full Portfolio Evaluation

Amaç

“Demo güzel” seviyesinden çıkıp tüm müşteri kohortu üzerinde sistemin gerçekten ne verdiğini görmek.

Çok önemli not

Burada senin özellikle istediğin şeyi ekliyorum:

eldeki tüm müşterileri modele sokup çıktıları incelemeliyiz

Bu faz kesinlikle yapılmalı.

Yapılacaklar
	1.	Tüm Lending Club / mevcut müşteri dataset’ini full inference’a sok
	2.	Her müşteri için:
	•	plan üretildi mi
	•	plan türü
	•	feasibility
	•	trajectory
	•	offer var mı
	•	execution probability
	3.	Coverage analizi yap
	4.	Segment bazlı analiz yap
	•	income band
	•	risk band
	•	stress band
	5.	Full portfolio validation raporu üret

Ölçülecekler
	•	plan coverage
	•	feasible plan rate
	•	execution-weighted expected improvement
	•	offer coverage
	•	offer acceptance distribution
	•	trajectory checkpoint health
	•	governance-safe plan rate
	•	learning readiness coverage

Başarı kriterleri
	•	sistemin “tüm müşteri evreninde” nasıl davrandığı görülür
	•	demo ile gerçek coverage arasında fark varsa anlaşılır
	•	ürünün gerçekten istenen çıktıları sağlayıp sağlamadığı ölçülür

⸻

Phase 33 — UAT & Analyst Workflow

Amaç

Gerçek kurum kullanıcıları için kullanılabilirlik testi yapmak.

Yapılacaklar
	1.	10 maddelik UAT checklist oluştur
	2.	Analist workflow testi yap
	3.	Demo center değil, gerçek analyst task akışı kur
	4.	“Bu müşteri için ne önerirsin?” testleri yap
	5.	“Bu teklifi neden önerdin?” testleri yap
	6.	Feedback’leri ürün ve model tarafına geri besle

Başarı kriterleri
	•	ürün sadece güzel görünmez, gerçekten kullanılabilir olur
	•	analyst personas için yeterince anlaşılır hale gelir

⸻

Phase 34 — Pilot Readiness

Amaç

Gerçek pilot müşteri veya kurum demosuna çıkacak seviyeye gelmek.

Yapılacaklar
	1.	Domain, hosting, production deploy
	2.	Logging / monitoring / analytics
	3.	Demo request pipeline
	4.	Pilot dataset workflow
	5.	Curated institution-specific demo flows
	6.	Sales deck + proof deck + investor deck
	7.	Security / auth / basic ops readiness
	8.	Pilot-specific configuration layer

Başarı kriterleri
	•	kurumsal demo güvenle gösterilebilir
	•	lead capture çalışır
	•	ürün ve web birlikte çalışır
	•	ilk pilot için sunulabilir hale gelir

⸻

Öncelik sırası

Eğer hepsini bir anda yapmayacaksan, doğru sıra şu:

En kritik ilk sıra
	1.	Phase 1 — Action Semantics
	2.	Phase 3 — Behavior-Aware Recourse
	3.	Phase 4 — Trajectory Planning
	4.	Phase 5–7 — Offer Layer
	5.	Phase 16 — Full Portfolio Evaluation
	6.	Phase 11–12 — Website Repositioning + Demo Refactor

İkinci sıra
	7.	Phase 8–10 — Learning Loop
	8.	Phase 13–15 — Proof/Investor/Web foundation
	9.	Phase 17–18 — Pilot readiness

⸻

En kritik eksikler — tek listede

Model tarafı
	•	feature output → real action translation eksik
	•	execution probability eksik veya yüzeye yeterince yansımıyor
	•	partial execution semantics tam ürünleştirilmeli
	•	offer layer tam ticari objective ile oturmalı
	•	portfolio-wide analysis yapılmalı
	•	full cohort validation şart
	•	learning loop artifact’leri policy insight’a bağlanmalı

Web tarafı
	•	kurum alıcısı önceliği tam uygulanmalı
	•	demo engine output hissinden çıkmalı
	•	proof, governance ve trust daha görünür olmalı
	•	investor sayfası daha net kategori anlatmalı
	•	website full-stack skeleton kurulmalı
	•	curated demo data pipeline şart
	•	tüm müşteri çıktılarının analizinden gelen gerçek proof yüzeye taşınmalı

⸻

Çok kısa sonuç

Bu roadmap sonunda proje şu dönüşümü yaşar:

Bugün

Güçlü ama kısmen teknik bir credit decisioning + recourse engine

Sonra

Davranışa duyarlı, teklif optimize eden, öğrenebilen, kurum alıcısına satılabilir, proof-supported bir decision platform

⸻
