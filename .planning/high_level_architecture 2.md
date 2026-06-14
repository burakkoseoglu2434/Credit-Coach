# Yüksek Seviye Sistem Mimarisi (High-Level Architecture)

Credit Coach sisteminin uçtan uca akışı, veri girişinden nihai sunum ekranlarına kadar 5 ana katmana ayrılır. Aşağıdaki diyagram, bu katmanlar arasındaki ilişkiyi ve veri akışını özetlemektedir.

```mermaid
graph TD
    %% Styling Colors
    classDef data fill:#2D3047,stroke:#fff,color:#fff;
    classDef model fill:#1B998B,stroke:#fff,color:#fff;
    classDef engine fill:#E84855,stroke:#fff,color:#fff;
    classDef presentation fill:#FFB703,stroke:#333,color:#333;
    classDef validation fill:#FB8500,stroke:#333,color:#333;

    %% Data Processing Layer
    subgraph DataPipeline ["Data Pipeline"]
        direction TB
        A["Raw Data"]:::data --> B["Feature Engineering\n(48 Feature Lock)"]:::data
    end

    %% Model Layer
    subgraph CoreMLModel ["Core ML Model"]
        direction TB
        B --> C{"Risk Model\n(XGBoost / LR)"}:::model
        C --> D["Raw PD\n(Probability of Default)"]:::model
        D --> E["Calibration Engine\n(Isotonic / Sigmoid)"]:::model
        E --> F["Calibrated PD &\nConfidence Intervals"]:::model
    end

    %% Engine / Recourse Layer
    subgraph DecisionEngine ["Decision & Planning Engine (from Phase 12-42)"]
        direction TB
        F --> G{"Decision Gate\n(Threshold/Tau)"}:::engine
        G -- "APPROVED" --> H["Direct Approval"]:::engine
        G -- "REJECTED" --> I["Recourse Generation\n(DiCE + Heuristics)"]:::engine
        I --> J["Action Semantics\nTranslation"]:::engine
        J --> K{"Feasibility Engine\n(Validity Check)"}:::engine
        
        K -- "valid / clipped / provisional" --> L["Execution Modeling\n(Difficulty & Cost)"]:::engine
        K -. "invalid" .-> O["Fallback & Diagnostics"]:::engine
        
        L --> M["Offer Optimization\n(Institution Support)"]:::engine
        M --> N["Trajectory Planning\n(4, 12, 24 weeks)"]:::engine
        
        N --> P["Final Plan & Status\n(Winner Integrity)"]:::engine
        H --> P
        O -.-> P
    end

    %% Presentation Layer
    subgraph PresentationLayer ["Presentation & Output"]
        direction TB
        P --> Q["Narrative Generation"]:::presentation
        Q --> R1["Operator Packet"]:::presentation
        Q --> R2["Customer Summary / UI"]:::presentation
    end

    %% Validation Layer
    subgraph ValidationLayer ["Portfolio Audit"]
        P -. "Batch Output" .-> S["Portfolio Validation &\nCoverage Audit"]:::validation
    end
```

---

## Bileşenlerin Görevleri ve Açıklamaları

### 1. Veri Katmanı (Data Pipeline)
Analiz için 48 özellik kilidinin işletildiği ana merkezdir. Müşteri verileri, algoritmaların tutarlı kararlar alabilmesi için temizlenir ve kilitli özellik setine çevrilir.

### 2. Çekirdek Model (Core ML Model)
Tahmin yapan motordur. **XGBoost** veya **LR** ile kişinin geri ödeyememe ihtimali (PD) sayısal olarak bulunur. Isotonic ve Sigmoid **kalibrasyon** adımlarıyla bu oranların gerçekliği artırılır. Kesin rakam yerine "güven bandı" ile desteklenen PD üretilir.

### 3. Karar ve Planlama Motoru (Decision & Planning Engine)
**Sistemin kalbini oluşturan katmandır.** "Bu kişi reddedildi, peki ne yaparsa onaylanır?" sorusuna yanıt üretilir:
- **Recourse Generation (DiCE vb.):** Farklı olasılıklar kurgulayarak bir alternatif kurtarma planı (action plan) üretir.
- **Action Semantics:** `"Mevcut kart limiti kullanımı %85'ten %40'a düşmeli"` denilen teknik ifadeyi business anlayışına ("Kredi kartı kullanılabilirliğini artır.") çevirir.
- **Feasibility Engine & Execution:** Hedeflenen plan işe yarar olabilir ama "gerçekte uygulanabilir mi?", maliyeti ve ağırlığı nedir diye tartılır.
- Burada bir hard-stop olan **Winner Integrity** kalkanı sayesinde hatalı, mantıksız (invalid) hiçbir plan dışarı aktarılmaz.

### 4. Sunum ve Çıktı (Presentation & Output)
Tüm karmaşık analiz verileri; iş/yatırım dili ve nihai müşteri arayüzü formlarına dökülür. **Narrative Generation** sayesinde müşteri planları, analistin inceleyeceği paket (Operator Packet) dili oluşturulup dışarı servis edilir.

### 5. Portföy Kontrolü (Portfolio Validation)
Geliştirilen sistemin sadece tek kişide harika karar vermekle kalmayıp kitlesel olarak (örneğin 100 kişi için) tutarlı oranlarda kalıp kalmadığını, hangi segmentleri kapsadığını ve ne denli başarılı "gerçekleştirilebilir" aksiyonlar yarattığını izleyen batched mekanizmadır.
