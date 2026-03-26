# Portföy ve Pilot Simülasyon Akışı (Data Flow)

Bu veri akış (Data Flow) diyagramı, Credit Coach sisteminin tek bir müşteri yerine toplu portföy verileri (Parquet/CSV) ile çalışırken pilot simülasyonları **(Batch Processing)** nasıl yürüttüğünü ve başarısını nasıl kanıtladığını gösterir.

```mermaid
graph TD
    classDef data fill:#2D3047,stroke:#fff,color:#fff;
    classDef process fill:#1B998B,stroke:#fff,color:#fff;
    classDef aggregation fill:#E84855,stroke:#fff,color:#fff;
    classDef metric fill:#FFB703,stroke:#333,color:#333;

    subgraph Data Input ["Pilot Data Source"]
        A[/"Test Portföyü / Pilot Data\n(credit-coach/data/.../.parquet)"/]:::data
    end

    subgraph Pipeline ["Batch Processing Pipeline"]
        direction TB
        A --> B["Batch Runner\n(Toplu Müşteri Tarama)"]:::process
        B --> C["Core Decision Engine\n(Model + Recourse + Feasibility)"]:::process
        C --> D[/"Bireysel Müşteri Çıktıları\n(Karar JSON'ları ve Metrikleri)"/]:::data
    end

    subgraph Aggregation ["Aggregation & Portfolio Logic"]
        direction TB
        D --> E{"Portfolio Validator\n(Kümülatif Analiz Motoru)"}:::aggregation
    end

    subgraph Metrics ["Evaluation Metrics (Performans Ölçümleri)"]
        direction TB
        E --> F1["Decision Funnel\n(Kapsama Oranı)"]:::metric
        E --> F2["Realization Share\n(Kurum Teklifi / Gerçekleşme Faydası)"]:::metric
        E --> F3["Calibration Review\n(Aşırı İyimserlik Kontrolü)"]:::metric
        E --> F4["Segment Performance\n(Hangi Kitlede Daha İyi)"]:::metric
    end

    subgraph Reports ["Final Reporting Outputs"]
        direction TB
        F1 --> R1[/"Portfolio Metrics Report\n(Toplu Performans Metrikleri CSV)"/]:::data
        F2 --> R1
        F3 --> R1
        F4 --> R1
        R1 --> R2[/"Operator & Executive Briefing\n(Yönetici Özeti)"/]:::data
    end
```

---

## Veri Akışı Aşamaları (Notes)

### 1. Data Input (Pilot Veri Kaynağı)
Uygulama canlıya alınmadan önce, gerçeğe çok yakın temizlenmiş müşteri verilerini içeren Parquet veya CSV dosyaları (`test.parquet`) sisteme sunulur. Bu, 50, 100 veya 10.000 müşteriyi içerebilir.

### 2. Batch Processing Pipeline (Toplu İşlem)
`Batch Runner`, tek tek binlerce müşteriyi Credit Coach'un kalbine (**Core Decision Engine**) sokar. 
*   Her bir kişi için Risk Hesabı, Recourse İhtimali ve Feasibility değerlendirilir.
*   Her kullanıcı için süreç tamamlandığında sistem bireysel *Artifacts* (tekil log ve JSON dosyaları) basar. 

### 3. Aggregation (Toplama ve İnceleme)
`Portfolio Validator` katmanı, alt tarafta 1000 ayrı `CONDITIONAL` veya `REJECTED` var ise bunları toplar. Amacı şudur: *"Evet, tek bir kişide güzel plan önerdik ama acaba bu 1000 kişinin %90'ına aşırı iyimser (yapılamaz) tavsiyeler mi verdik?"* sorusunu sormak.

### 4. Evaluation Metrics (Performans Ölçümleri)
Bu aşamada şu metrikler veri hattından geçer:
*   **Decision Funnel:** Giren müşteri sayısının yüzde kaçına `APPROVED`, kaçına kurtarma (`CONDITIONAL`), kaçına `REJECTED` denildiği.
*   **Realization Share:** Önerilerin gerçek maliyet-fayda analizi. Kurum tekliflerinin (Offer) genel iyileşmedeki payı.
*   **Calibration Review:** Sonuçların veriye ve gerçeklere ne kadar uygun olduğu kontrol edilir (Aşırı iyimserlik filtrelenir).

### 5. Final Reporting (Çıktı ve Raporlama)
Tüm bu istatistikler toplanarak yöneticiler için **Executive Briefing** dokümanlarına ve iş zekası araçlarında kullanılabilecek Portfolio Metrik raporlarına (/`data/processed/...` output dosyalarına) kaydedilir.
