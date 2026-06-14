# Model ve Recourse Etkileşim Akışı (Sequence Diagram)

Bu diyagram, Credit Coach sistemine bir risk inceleme isteği (örneğin API üzerinden) geldiğinde, müşterinin otomatik onay almaması (`REJECTED` bandında kalması) koşulunda sistemin **kurtarma planlarını (Recourse)** nasıl tetiklediğini ve son karar özetini nasıl oluşturduğunu adım adım (zaman çizelgesinde) göstermektedir.

```mermaid
sequenceDiagram
    participant CLI as İstek (API/Batch)
    participant RM as Risk Model & Kalibrasyon
    participant DE as Karar Motoru (Tau)
    participant RP as Recourse Planner (DiCE)
    participant FC as Feasibility & Execution
    participant OE as Kurum Teklifi (Offer)
    participant NG as Sunum (Narrative)

    CLI->>RM: 1. Müşteri Verisini İncele
    activate RM
    RM->>RM: 2. PD (Geri Ödeyememe Riski) ve Kalibrasyon Hesapla
    RM-->>DE: 3. Kalibre Edilmiş Risk Puanını İlet
    deactivate RM

    activate DE
    DE->>DE: 4. Risk / Eşik (Tau) Kontrolü
    alt Müşteri Onaylandı ("APPROVED")
        DE-->>CLI: 5. Sonuç: APPROVED (Erken Dönüş)
    else Müşteri Reddedildi ("REJECTED")
        DE->>RP: 6. Alternatif Kurtarma Planı (Recourse) Talep Et
        activate RP
        RP->>RP: 7. DiCE + Uzman Kuralları ile Aday Planlar Üret
        RP-->>FC: 8. Üretilmiş Aday Plan Havuzunu Gönder
        deactivate RP

        activate FC
        FC->>FC: 9. Mantıksız Planları Temizle (Validity / Hard Stop)
        FC->>FC: 10. Yapılabilirlik Zorluğunu (Difficulty) Modelle
        FC-->>OE: 11. Yalnızca Geçerli Adayları İlet
        deactivate FC

        activate OE
        OE->>OE: 12. Kurum Destekleri Varsa Planlara Ekle (Taksit vb.)
        OE-->>NG: 13. En İyi 'Geçerli' Kazananı Seç (Winner Integrity)
        deactivate OE

        activate NG
        NG->>NG: 14. Sayısal Hedefleri İş Diline (Semantics) Çevir
        NG->>NG: 15. Operatör Paketi (Operator Packet) Çıktılarını Hazırla
        NG-->>CLI: 16. Nihai Sonucu ("CONDITIONAL/REJECTED" + Winner Plan) Dön
        deactivate NG
    end
    deactivate DE
```

---

## Sıralı Katmanların Görevleri (Notes)

### 1-5 Arası (Risk Değerleme & Basit Onay):
Müşteri verisinin girip ilk "karar/eşik (Tau)" duvarına çarptığı yer burasıdır.
Model, `XGBoost` üzerinden tahminleme yapar. Kalibrasyon sonrasında müşteri risk puanı eşiğin altındaysa, **Recourse katmanları (DiCE vs.) boşa çalıştırılmadan ("APPROVED" cevabıyla) doğrudan geri dönülür.**

### 6-9 Arası (Recourse & Feasibility / Kurtarma):
Eğer profil `REJECTED` bölgesindeyse sistem devreye girer:
*   Müşterinin "borç azaltımı", "kredi kartı kapama" ihtimalleri (DiCE) ve uzman kuralları hesaplanarak bol miktarda **Aday Plan** (Candidate Pool) türetilir.
*   **Feasibility (Yapılabilirlik):** Anormal planlar `invalid` olarak işaretlenip (Hard Stop) çöpe atılır, sadece "yapılabilir" planlar (geçerli/provisional) yaşamaya devam eder. (Bkz: Phase 45 Winner Integrity mantığı)

### 10-13 Arası (Execution & En İyi Seçim):
*   Geriye kalanların "ne kadar sürede/maaliyetle" (Execution Difficulty) başarılabileceği çıkarılır.
*   Eğer banka ya da kurum **Özel Bir Teklif** (örneğin %10 indirim veya taksitlendirme) girmişse plana o da yapıştırılır.
*   Bu filtrenin ardından Winner Integrity kurallarına uygun **Tek Bir Kazanan Plan** seçilir.

### 14-16 Arası (Anlatım ve Teslimat):
Makinenin dilindeki sayısal hedefler (`revol_util 68 -> 45`), gişe memurunun anlayacağı **Action Semantics ("Kredi kartı limitini artır / ödemeni düzelt")** metinlerine ve detaylı **Operator Packet** sunum dosyasına (JSON vb.) dönüşür ve istek tarafına (API/CLI) yanıt olarak iletilir.
