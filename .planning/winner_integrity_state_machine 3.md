# Karar Sahipliği ve "Winner Integrity" Durum Makinesi (State Machine)

Bu diyagram, sistem içerisindeki ham verilerin (Risk Modelinden çıkan sonuçlar ve DiCE üzerinden gelen aday planlar) sistemde hangi "internal" aşamalardan geçtiğini ve **v2.2 Milestone'unda çözülen en büyük sorunun (Phase 45-48)** sistemden dışarı sızacak verileri "Hard Stop" mantığıyla nasıl sınırlandırdığını anlatır.

```mermaid
graph TD
    classDef internal fill:#2D3047,stroke:#fff,color:#fff;
    classDef gateway fill:#E84855,stroke:#fff,color:#fff,stroke-width:3px;
    classDef public fill:#1B998B,stroke:#fff,color:#fff,stroke-width:2px;
    classDef surface fill:#FFB703,stroke:#333,color:#333;
    classDef error fill:#8B0000,stroke:#fff,color:#fff;

    A(("İstek (Müşteri)")):::internal --> B["Risk Modeli &\nEşik (Tau) Kontrolü"]:::internal
    
    B -- Risk Puanı İdeal --> C_APP["Internal:\n APPROVED Müşteri"]:::internal
    B -- Risk Puanı Kötü --> C_REC["Internal:\n Kurtarma Planı İhtiyacı"]:::internal
    
    C_REC --> C_POOL["Aday Plan Havuzu\n(DiCE & Uzman Hedefleri)"]:::internal
    
    C_POOL -- Mantıksız Çıkanlar (Gerçek Rakam Değil) --> S_INV["Internal:\n Invalid Plans"]:::internal
    C_POOL -- Yeni Filtre Öncesi Alternatifler --> S_FALL["Internal:\n Fallback Pools"]:::internal
    C_POOL -- Gerçek Hayatta Yapılabilir Çıkanlar --> S_VAL["Internal:\n Valid / Provisional Plans"]:::internal

    %% Phase 45-48 Gate
    GATE{"Phase 45-48 Hard Stop\n(Winner Integrity Gating)"}:::gateway

    C_APP --> GATE
    S_INV -->|Asla Sızamaz / Çöpe Atılır| GATE
    S_FALL -->|Eğer Geçerli Yoksa Bekler| GATE
    S_VAL -->|Geçerli İse Değerlendirilir| GATE

    %% Public End States
    GATE -- İçeride Geçerli Bir Winner\nPlan Bulunamadıysa --> P_REJ["Public Karar:\n REJECTED"]:::public
    GATE -- İçeride Yapılabilir ve Gerçekçi\nBir Kazanan (Winner) Varsa --> P_CON["Public Karar:\n CONDITIONAL"]:::public
    GATE -- Başlangıçta Doğrudan Geçenler --> P_APP["Public Karar:\n APPROVED"]:::public
    
    %% Internal Errors
    GATE -. Sistem İstisnası veya Bug .-> E_REV["Internal Exception:\n NEEDS_REVIEW"]:::error

    %% Consumption Surfaces
    P_APP --> SUR1["Operator Short View\n(Gişe Arayüzü / Operatör)"]:::surface
    P_CON --> SUR1
    P_REJ --> SUR1

    P_APP --> SUR2["Decision Summary\n(Final Müşteri Çıktısı)"]:::surface
    P_CON --> SUR2
    P_REJ --> SUR2

    P_APP --> SUR3["Portfolio Metrics\n(Toplu Performans Metrikleri)"]:::surface
    P_CON --> SUR3
    P_REJ --> SUR3
```

---

## Katmanların Özeti ve Roller (Notes)

### 1. Internal States (İç Durumlar)
Müşteri için henüz kesin ve herkesin önünde ilan edilecek bir sonuç yoktur. Bu aşamada sistem olasılıkları tarar:
*   Müşteri doğrudan onaylı havuzda olabilir.
*   Geçersiz sayısal varyasyonlar yüzünden `Invalid Plans` sepetine malzeme yığılmış olabilir.
*   Elde geçerli sonuç yoksa sistem eski `Fallback Pools` tarafında dolaşıyor olabilir.
*   **Aman Dikkat:** Bu evre kapalı kapılar ardındadır.

### 2. Hard Stop / Gate (Phase 45-48 Kuralları)
v2.2 (Winner Integrity) sürümünün en büyük vaadidir. 
*   Geçersiz (invalid) çıkan veya DiCE'ten gelen ama saçma olan hiçbir plan dışarıdaki yüzeylere *sızamaz*. 
*   Eğer bir plan geçerli değilse, sistem o planı "kurtarma" bahanesiyle diriltmez. Planı atar ve eğer başka geçerli seçenek kalmadıysa, sonucu zorla CONDITIONAL yapmak yerine dürüstçe REJECTED üretir.

### 3. Public Final States (Dışarıya Gösterilen Durumlar)
Bu noktada karar mühürlenir. Web sitesine, operatöre ya da final log dosyasına yansıyacak sadece üç net karar (Business-visible states) çıkar:
*   **APPROVED:** Onaylandı.
*   **CONDITIONAL:** Onaylanmadı ama uygulanabilir geçerli bir planı var.
*   **REJECTED:** Onaylanmadı ve gerçekleştirilebilecek mantıklı/geçerli bir kurtarma planı da maalesef bulunamadı.
*   **NEEDS_REVIEW:** Dışa dönük bir karar değildir, içeride kalan ve incelenmesi gereken sistem bug / hata durumlarını toplar (Bu bir Public state değildir!).

### 4. Erişen Yüzeyler (Consumer Surfaces)
Mühürlenen karar, projenin her köşesinde aynı (tek doğrulu) sonucu gösterir:
1.  **Operator Short View:** Ekranın en tepesinde yeşil/sarı/kırmızı olarak gözükür ve sadece 'Geçerli' olan planı öneri olarak sunar.
2.  **Decision Summary:** En son log dosyasındaki JSON ya da CSV satırlarında da aynı ibare ve açıklama bulunur.
3.  **Portfolio Metrics:** Günün sonunda yöneticilere gidecek raporlarda, 100 kişinin kaçı REJECTED, kaçı CONDITIONAL oldu diye tutarlıca toplanır. Bir yerdeki CONDITIONAL plan durumu, başka yerde REJECTED görünmez (Consistency).
