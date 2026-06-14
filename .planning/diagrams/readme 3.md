Credit Coach - Önerilen Mimari Diyagramlar
Tüm projeyi (özellikle 
PROJECT_REHBERI_TR.md
, 
ROADMAP.md
 belgelerini ve credit-coach/src/credit_coach modül yapısını) inceledim. Credit-Coach sadece basit bir makine öğrenmesi modeli değil; içinde çok sayıda karar katmanı (Model, Recourse, Feasibility, Execution, Offer, Portfolio) barındıran kompleks ve 10 katmanlı bir Karar Destek Motoru (Decision Engine).

Bu yapının karmaşıklığını hem teknik ekibe, hem iş birimlerine, hem de yatırımcılara (Investor Brief / Pilot aşamaları) net aktarabilmek için aşağıdaki 5 Temel Diyagramı çizmende büyük fayda var (Dilersen bunları senin için draw.io ile ben de çizebilirim):

1. Yüksek Seviye Sistem Mimarisi (High-Level Architecture)
Amacı: Model ile kural tabanlı katmanların (Engine) farkını ve veri akışını göstermek. İdeal Format: Flowchart / Architecture Diagram İçermesi Gereken Bloklar:

Veri Katmanı: 48 Feature Lock, Veri Temizleme.
Model Katmanı (Tahmin): XGBoost / Logistic Regression -> PD (Probability of Default) -> Calibration (Isotonic/Sigmoid) -> Conformal Intervals.
Karar & Planlama Katmanı (Engine): Threshold (Tau) uygulanması -> Recourse (DiCE + Heuristics) -> Feasibility Engine (validity check) -> Execution Modeling -> Offer (Kurum Teklifleri).
Sunum Katmanı: Narrative Generation -> Operator Packet / API / Website.
2. Model ve "Recourse Planner" Etkileşimi (Sequence Diagram)
Amacı: Sadece red alan (riskli) bir müşteri içeri girdiğinde sistemin nasıl bir "kurtarma planı" (Recourse) ürettiğini sırasıyla göstermek. İdeal Format: Sequence / Swimlane Diagram Adımlar:

Müşteri verisi girer.
Model riski hesaplar (Örn: %80 PD -> Red).
coaching / recourse modülü devreye girer.
Hem içeriden (heuristics) hem de DiCE üzerinden alternatif senaryolar (Aktion Semantics: revol_util 68 -> 45) üretilir.
policy/decision modülleri bu hedeflerin gerçekçi olup olmadığını (valid, clipped, invalid vb.) test eder.
Geçerli olan "En İyi Aksiyon Planı" seçilir.
3. Karar Sahipliği ve "Winner Integrity" Durum Makinesi (State Machine)
Amacı: Müşterinin sistem içindeki nihai durumunun (Business-visible decision) nasıl belirlendiğini ve dışarıya nasıl yansıdığını sabitlemek (Özellikle v2.2 Milestone'unda çözülen sorunlar). İdeal Format: State Diagram / Flowchart Durumlar:

Internal States: NEEDS_REVIEW, Invalid Plans, Fallback Pools.
Hard Stop / Gate: Phase 45-48 kuralları (Geçersiz hiçbir plan dışarı sızamaz, DiCE dahil).
Public Final States: APPROVED, CONDITIONAL, REJECTED.
Erişen Yüzeyler: Operator Short View, Decision Summary, Portfolio Metrics.
4. Portföy ve Pilot Simülasyon Akışı (Data Flow)
Amacı: Sistemin tek bir müşteri için değil, 100 kullanıcılık bir test portföyünde (Batch Processing) nasıl çalıştığını yatırımcıya veya bankaya göstermek. İdeal Format: Pipeline / Data Flow Diagram İçermesi Gereken Bloklar:

Batch input data (Pilot Data).
Parquet dosyalarının işlenmesi (credit-coach/data/processed/test.parquet).
Toplu değerlendirme metriklerinin hesaplanması (Kapsama oranı, gerçekleşme olasılığı, offer support rate).
Çıktı raporlaması (Portfolio Validation Metrics).
5. Klasör & Modül Bağımlılık Haritası (Component Diagram)
Amacı: Geliştiricilerin (veya sonradan projeye dahil olanların) kod bazında hangi modülün ne iş yaptığını anlamasını sağlamak. İdeal Format: UML Component Diagram Klasörler ve Roller:

model/: Kalibrasyon ve tahmin.
recourse/ & causality/: Alternatif senaryo üretimi.
coaching/: Action Semantics, execution modeling, offer optimizasyonu.
decision/ & policy/: Validity, kurallar ve durum makinesi sahipliği.
portfolio/ & evaluation/: Çıktıların validasyonu ve portfolio analizi.
api/ & app/: Sunum yüzeyleri.