# Klasör & Modül Bağımlılık Haritası (Component Diagram)

Bu (Bileşen/Klasör) diyagramı, `credit-coach/src/credit_coach` altındaki ana modüllerin birbirleriyle olan hiyerarşik ilişkisini ve Credit Coach'un temel sorumluluklarını hangi klasörlere dağıttığını gösterir. Özellikle projeye yeni katılan geliştiriciler için **kod hizalanması (codebase onboarding)** rehberidir.

```mermaid
graph TD
    classDef pres fill:#FFB703,stroke:#333,color:#333;
    classDef core fill:#E84855,stroke:#fff,color:#fff;
    classDef plan fill:#1B998B,stroke:#fff,color:#fff;
    classDef coa fill:#2D3047,stroke:#fff,color:#fff;
    classDef mod fill:#6C757D,stroke:#fff,color:#fff;
    classDef eval fill:#FB8500,stroke:#333,color:#333;

    %% Modüller
    P_API["api/ & app/\n(Sunum Yüzeyleri & Giriş)"]:::pres
    
    C_DEC["decision/ & policy/\n(Kurallar, Hard-Stop ve Durum Makinesi)"]:::core
    
    P_REC["recourse/ & causality/\n(DiCE ve Alternatif Senaryo Üretimi)"]:::plan
    P_COA["coaching/\n(Action Semantics, Zorluk & Teklifler)"]:::coa
    
    M_MOD["model/\n(XGBoost Tahmin ve Kalibrasyon)"]:::mod
    
    E_POR["portfolio/ & evaluation/\n(Toplu Performans ve Analiz)"]:::eval

    %% Bağlantılar (Etkileşim Akışı)
    P_API -->|"1. API İsteği & Sonuç"| C_DEC
    
    C_DEC -->|"2. Modelden Risk Olasılığı İster"| M_MOD
    C_DEC -->|"3. Kurtarma Gerekirse Plan İster"| P_REC
    C_DEC -->|"5. Plan Geçerliliğini & Semantiğini Sorar"| P_COA
    
    P_REC -->|"4. Planların Etkisini Simüle Eder"| M_MOD
    
    E_POR -.->|"6. Test Portföyüyle Sistemi Dener"| C_DEC
    E_POR -.->|"7. Üretilen Cümleleri Denetler"| P_COA
```

---

## Klasörlerin Görevleri (Notes)

### 1. `api/` & `app/` (Sunum Yüzeyleri)
Dış dünyanın veya web arayüzünün (Credit-Coach Website) sisteme temas ettiği katmandır. Müşteri verisi REST API / CLI üzerinden buraya ulaşır; ancak bu modüllerin kendi başına bir karar yetkisi yoktur, sadece `decision` katmanına aracılık eder.

### 2. `decision/` & `policy/` (Orkestrasyon ve Durum)
Uygulamanın orkestra şefi ve kural koyucusudur. Onay (`Tau`) sınırlarının uygulandığı, Winner Integrity (Phase 45-48 Hard Stop Kuralları) mantıklarının kilitlendiği ana yerdir. Diğer modülleri çağırır, çıkan cevabın dışarıya sızıp sızmayacağına burası karar verir (`APPROVED`, `REJECTED`, `CONDITIONAL`).

### 3. `model/` (Tahmin Motoru)
Sadece risk hesabına (PD) odaklanır. Veriyi XGBoost veya Linear modellere sokar, kalibrasyonu yapar ve salt bir güvenlik puanı çıkartır. İçerisinde iş kuralı barındırmaz.

### 4. `recourse/` & `causality/` (Planlama Laboratuvarı)
Machine Learning destekli planlama ajanı (DiCE) burada koşar. Yüksek riskli profili onaylanabilir bir profile dönüştürmek için matematiksel permütasyonlar dener ve bol miktarda ham senaryo çıkartır.

### 5. `coaching/` (Çevirmen ve Fizibilite)
Sayıları insan diline ve gerçek dünyaya bağlar.
*   **Action Semantics:** Dönen sayıları ("Feature X %20 artmalı") -> ("Limitsiz kredi kullanımını azalt") cümlesine döndürür.
*   **Execution & Feasibility:** Senaryonun aslında mantıksız olup olmadığı, çok para/zorluk gerektirip gerektirmediği yine burada hesaplanır.

### 6. `portfolio/` & `evaluation/` (Denetçi)
Hiçbir tekil müşteriye (canlı sisteme) doğrudan karışmaz. Çevrimdışı (Offline) çalışarak `test.parquet` gibi dev verileri sisteme sokar ve sistemin genel mantıksal performansını / kapsama oranlarını ölçer.
