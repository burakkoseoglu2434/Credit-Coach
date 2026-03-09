# Credit Coach: Junior Developer Onboarding Rehberi

Hoş geldin! Bu doküman, Credit Coach projesinin ne olduğunu, hangi teknolojileri kullandığını, mimari tasarım kararlarımızı ve projenin gelişim sürecini uçtan uca anlatmak için hazırlandı. Kodu okumaya başlamadan önce bu belgeyi baştan sona okuman, sistemin *nasıl* değil, *neden* böyle yazıldığını anlaman için çok kritik.

---

## 1. Biz Ne Yapıyoruz? (Proje Vizyonu)

**Geleneksel Kredi Modelleri:** Geleneksel bankacılık, "Bu müşteriye kredi verelim mi?" sorusuna sadece *Evet* (Approved) veya *Hayır* (Denied) yanıtı verir. Müşteri reddedildiğinde neden reddedildiğini veya onay almak için ne yapması gerektiğini bilmez. Sadece "Risk Puanınız Düşük" gibi kapalı kutu (black-box) yanıtlar alır.

**Credit Coach (Bizim Yaptığımız):** Biz, sadece müşterinin "Red/Onay" durumunu (PD - Probability of Default) tahmin eden bir ML Modeli yapmıyoruz. Biz, **reddedilen müşteriye "Şu 3 eylemi yaparsan (örneğin X kartını kapat, Y borcunu öde) 6 ay sonra kredi alabilirsin" diyen bir Finansal Danışman (Recourse / Yönlendirme Algoritması) geliştiriyoruz.**

Sistemin temel felsefesi şudur: *Karar adil (fair), uygulanabilir (feasible), güvenilir (robust) olmalı ve sadece tek seferlik değil, zamana yayılan (trajectory) bir yol haritası sunmalıdır.*

---

## 2. Mimariye Genel Bakış (Klasörler ve Modüller)

Proje, production seviyesinde bir MLOps ve finansal teknoloji uygulaması olarak tasarlandı.

- `configs/`: Tüm mantık parametrik çalışır. Hiçbir özellik kodun içine (hardcode) yazılmaz. Modeller, karar sınırları (tau), şok senaryoları `recourse.yaml` veya `model.yaml` üzerinden okunur.
- `src/credit_coach/data/`: `schema.py` dosyası projenin kalbidir. Pydantic v2 kullanarak müşterinin (`CustomerSnapshot`), çıkartılan planın (`PlanRecord`) ve kararların (`DecisionOutcomeRecord`) tip onaylarını (type validation) yapar.
- `src/credit_coach/storage/`: Pydantic objelerini SQLAlchemy aracılığıyla (SQLite/PostgreSQL) veritabanına kaydeder (`models.py`, `repository.py`). Kriptografik özetlemelerle (hash chaining) hiçbir kaydın sonradan habersiz değiştirilemeyeceği **Audit Trails** yapısını barındırır.
- `src/credit_coach/model/`: Veriyi (`ingest.py`, `split.py`) alır, XGBoost ile eğitir ve kalibre eder.
- `src/credit_coach/evaluation/`: Fairness (Adalet) ve Offline Policy Evaluation (OPE) gibi metrik testlerini barındırır.
- `src/credit_coach/recourse/`: Projenin beyni! Modeli tersine çevirerek "Ne değişirse sonuç değişir?"i bulan kısımdır. Action Space (Müşteri neyi ne kadar değiştirebilir?), Feasibility (Bu eylem mantıklı mı?) ve Generator (Plan üreten motor) burada yaşar.
- `src/credit_coach/coaching/`: Üretilen planları inceleyen (Reviewer), iş kurallarına/stres testlerine vuran ve haftalık planlara çeviren (Planner) kısımdır.

---

## 3. Hangi Teknolojileri ve Modelleri Kullandık?

1. **Tahminleyici ( Predictive Model ): XGBoost**
   - Kararlı, tabüler veride (LendingClub veri seti) hızlı ve şeffaflığı kontrol edilebilir olduğu için kullanıldı. Ağırlıklı monotonik kısıtlar (monotone constraints) eklendi (örneğin: borç artarsa PD kesinlikle düşemez kuralı).
2. **Olasılık Kalibrasyonu: CalibratedClassifierCV (Isotonic Regression)**
   - XGBoost'un ham çıktılarını (0.4 veya 0.8), gerçek temerrüt etme ihtimalini ifade edecek "Kalibre Edilmiş Olasılık" (Probability of Default - PD) değerine çevirmek için kullanıldı.
3. **Açıklanabilirlik (Explainability): SHAP**
   - Müşterinin mevcut riskinin "neden" yüksek olduğunu anlamak (Local Feature Importance) için kullandık. SHAP değerleri planlama motorunu (hangi özelliğe saldırmalıyız?) yönlendirir.
4. **Çoklu Aday Üretimi (Counterfactuals): DiCE (Diverse Counterfactual Explanations)**
   - Müşteri için tek yönlü ve dar bir plan üretmek yerine "3 farklı alternatif senaryo" bulabilmek için Microsoft'un DiCE kütüphanesini sistemin destekleyici motoru olarak entegre ettik.
5. **Belirsizlik ve Stres Ölçümü: Conformal Prediction & Bootstrap**
   - Çıkarttığımız plan "ya tutmazsa?" sorusuna yanıt olarak, yapay zekanın her tahmininin yanına bir güven aralığı (Confidence Interval) ekledik. Böylece, makroyu veya model hatasını göz önüne alan **Worst-Case (En kötü senaryo) PD** (CVaR) oluşturduk.

---

## 4. Geliştirme Süreci (Neleri Değiştirdik?)

Yazılım döngüsü boyunca basit bir ML kodundan çok katmanlı, regülasyon uyumlu bir sisteme evrildik.
*   **V1 (Basit Recourse):** Sadece SHAP kullanıp, ağırlığı yüksek olan kolonu itiyorduk (Örn: Borcunu 1000 dolar kapat!). Bu, müşteriler için hayalci planlar üretiyordu.
*   **V2 (Robust Recourse & Action Space):** Her eyleme bir `cost` (maliyet), `time` (süre) ve sınırlama `min-max` ekledik. Optimizasyona **CVaR** mantığını ve **Conformal En Kötü Senaryo Risk Marjı** cezasını soktuk. (Sistemi güvenli hale getirdik).
*   **V3 (Trajectory Checkpoints):** İnsanlara "6 ay sonra şu hale gel" demek yerine, "İlk hafta hesabını kapat, 1. ayda borç/gelir oranını DTI<=30'a düşür, 6. ayda onay alacaksın" diyen **Aşamalı Yol Haritası (Trajectory)** altyapısını kurduk.
*   **V4 (Fairness Stabilizasyonu & OPE):** Cinsiyet/Irk/Gelir grupları arasında sistemin adaletsiz çalışmasını (recourse denial gap) engelleyecek **Fairness Guard** ekledik. Ayrıca "bu yapay zeka planı piyasada cidden çalışır mı?" sorusu için geçmiş veriyi kullanarak A/B testi simülasyonu yapan (OPE - Offline Policy Evaluation) sistemini kurduk. Sistemdeki her log sızdırılamaz (Cryptographic Hash) hale getirildi.

---

## 5. Sağladığımız Artışlar ve Başarı (ROI)

Testler (`run_batch_recourse_eval.py`) üzerinden net KPI'larımız şunlara ulaştı:
- **Denied-to-Approved Lift (Redden Onaya Dönüş):** %15'lerin üzerinde. Yani, geleneksel bankada reddedilecek yüksek riskli müşterilerin yaklaşık %15'i, bizim planlarımızı uygulayarak güvenli (default riski düşük) bir şekilde onay bandına geçiş yapabiliyor.
- **Fairness Stability (Adalet Stabilitesi):** Random seed kaynaklı kırılganlıklar giderildi. Gelir segmentleri ve risk segmentleri (Near/Mid/High) arasındaki "Recourse Başarı Farkı" (Gap) hedeflenen %10 sınırının çok altına (örneğin %1-2'lere) çekildi.
- **Latency (Hız):** Yüzlerce müşterinin planlarının her birini oluşturmak, DiCE ve Conformal Prediction'a rağmen **< 500 ms (p95)** sürelerine indirildi.
- **Çeşitlilik (Candidate Diversity):** Artık her müşteriye mekanik tek bir teklif değil, **En az 2 veya 3 farklı (biri zaman odaklı, biri maliyet odaklı) seçenek** rasyonel başarı esneklikleriyle birlikte sunuluyor.

---

## 6. Eksiklikler ve Sana Düşen Görevler (Gelecek Geliştirmeler)

Her modern sistem gibi bizim de teknik borçlarımız (technical debt) ve büyüme alanlarımız var. Yeni katılan bir Junior olarak göz atacağın ve geliştireceğin noktalar şunlardır:

1. **Feature Engineering (Özellik Mühendisliği) Genişletmesi:**
   Şu an 47 statik kolon üzerinden çalışıyoruz. Zaman serili özellikler (Time-Series Features) eklendiğinde (Müşterinin son 3 aydaki borç kapatma ritmi), XGBoost'u bırakıp bir RNN (LSTM) tabanlı model veya daha iyi bir TabTransformer mimarisine geçiş yapılabilir. *Bunu Recourse altyapısını bozmadan yapman gerekecek.*
2. **Large Language Model (LLM) Entegrasyonu:**
   Planları metne döküyoruz ama bir "chatbot" arayüzümüz eksik. Çıkan JSON formatındaki (`PlanRecord`) planların bir LLM ajanına beslenip, müşteriye "Merhaba ben sizin AI Finans Koçunuzum, bugün borç oranınızı %2 düşürecek şu teklifimiz var" diyerek RAG (Retrieval-Augmented Generation) altyapısı kurmak muazzam bir değer eklentisi olacaktır.
3. **DiCE Performans Darboğazları:**
   Bazen DiCE hesaplama yaparken hedeflenen süreyi aşabiliyor. `timeout` fall-back mekanizmasını yazdık ancak DiCE'ın kütüphane seviyesindeki yavaşlığını çözmek, daha hızlı "Gradient-based CF Generator"lara (PyTorch tabanlı) geçişi gerektirebilir.
4. **Makro (Macro-Economic) Modülün Dinamikleşmesi:**
   `macro.yaml` dosyasından statik okuduğumuz PMI/Enflasyon değişiklikleri şu an `stress_index` hesaplamasında temel. Ancak bunu canlı bir Merkez Bankası API'sine bağlayarak dinamik ekonomik zırhını (Live Monitoring) canlandırman harika olur.

---

Sistemin kalbini (Pydantic şemalarını, ActionSpace tanımlarını) bozmadığın sürece modülerlik sayesinde istediğin yeri geliştirip/büyütebilirsin. Bol şans, testleri çalıştırmadan commit atmamayı unutma! :)
