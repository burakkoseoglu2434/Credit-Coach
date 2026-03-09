# CREDIT COACH - 12 HAFTALIK AJAN DEVIR MASTER PLANI

## Surum
- Dokuman surumu: `v1.0`
- Hazirlanma tarihi: `2026-03-06`
- Kapsam: `Tez donemi 12 hafta + ajan devir kurallari`
- Yetki siniri: `Bu dokuman disina cikmak yasak`

---

## 1) Dokumanin Rolu ve Devir Sozlesmesi

Bu dosya, Credit Coach projesini bir ajanin uctan uca ve guvenli sekilde yurutmesi icin **tek operasyon kaynagi** olarak tasarlanmistir.

Bu dokumanin amaci:
1. 12 haftalik tum teknik isi adim adim tarif etmek.
2. Her hafta hangi algoritmalarin, hangi matematiksel ifadelerin ve hangi teknolojilerin kullanilacagini netlestirmek.
3. Kodu yazacak ajanin karar serbestligini azaltip, teknik sapmalari engellemek.
4. Akademik gecerlilik ve sektorel uygulanabilirlik arasinda denge kurmak.

Bu dokumanin baglayici kurallari:
1. Ajan bu dokumanin disinda yeni bir metodoloji uyduramaz.
2. Ajan burada yazmayan bir kritik modulu atlayamaz.
3. Ajan her hafta icin belirtilen cikti, test ve acceptance kosullarini saglamak zorundadir.
4. Belirsizlik varsa ajan varsayim yapmadan kullanicidan netlestirme istemelidir.

---

## 2) Proje Buyuk Resim

Tek cumle deger onerisi:

`Kredi alamayan musteriye, bankanin risk istahina ve makro kosullara gore dinamik olarak guncellenen, istatistiksel guvenlikli ve nedensel olarak tutarli iyilestirme plani sunmak.`

Iki katman:
1. `Research Core (Tez cekirdegi)`: PD modeli, SHAP, recourse, causal penalty, bootstrap CI, macro stress, fairness, benchmark, drift ve governance.
2. `Product Layer (MVP gecis zemini)`: policy engine, haftalik coaching loop, audit, portfolio impact, API/UI hazirligi.

---

## 3) Sabit Kisitlar ve Degismez Kurallar

1. `Config-first`: Tum parametreler YAML dosyalarindan gelir.
2. `Feature contract`: Su anki kod tabaninda veri sozlesmesi `47 feature + 1 target` seklindedir.
3. `Fail-fast`: Feature lock bozulursa pipeline durur.
4. `Traceability`: Her calisma `artifacts/runs/<run_id>/` altina snapshot ve metrik birakir.
5. `State ayrimi`: Egitim verisi dosyada; urun durumu DB'de tutulur.
6. `Status determinism`: Plan durumu sadece feasibility gate + istatistiksel guvenlik gate ile belirlenir.
7. `Dinamik kontrol zorunlulugu`: Haftalik coaching dongusunde statik plan yerine dinamik review/replan uygulanir.

---

## 4) Matematiksel Cekirdek (Global)

### 4.1 Risk modeli
\[
f(x, z_t) = P(Y=1 \mid x, z_t)
\]

- \(x\): musteri ozellikleri
- \(z_t\): zaman \(t\)'deki makro durum
- \(Y=1\): default/temerrut sinifi

### 4.2 Karar kurali
\[
\text{approve}(x) \iff f(x,z_t) \le \tau_t
\]

### 4.3 Recourse optimizasyonu
\[
\min_{x'} C(x,x')
\]
Kosullar:
\[
f(x', z_t) \le \tau_t,\quad x' \in \mathcal{A},\quad x' \in \mathcal{F}
\]

### 4.4 Plan maliyeti
\[
C(x,x')=\lambda_1\|x'-x\|_1+\lambda_2 \cdot Time(x,x')+\lambda_3 \cdot FinancialCost(x,x')
\]

### 4.5 Nedensel ceza
\[
Score = w_1(\tau_t - CI_{high}) + w_2R(x') - w_3C(x,x') - w_4CausalPenalty(A;G)
\]

- \(G\): causal graph (DAG)
- \(A\): aksiyon seti

### 4.6 Bootstrap guvenlik
\[
CI_{low}=Q_{\alpha/2}(p_b),\quad CI_{high}=Q_{1-\alpha/2}(p_b)
\]
\[
\text{APPROVED} \iff CI_{high} \le \tau_t
\]

### 4.7 Dinamik alpha
\[
\alpha(z_t)=
\begin{cases}
0.05, & MSI_t \le 0.7 \\
0.01, & MSI_t > 0.7
\end{cases}
\]

### 4.8 Makro sok guvenilirlik
\[
R(x')=\frac{1}{K}\sum_{s=1}^{K}\mathbf{1}[f(x', z_t^{(s)}) \le \tau_t^{(s)}]
\]

### 4.9 Haftalik ilerleme etiketi
\[
\Delta p_t = f(x_t,z_t)-f(x_{t-1},z_{t-1})
\]

- \(\Delta p_t < -\epsilon\): improving
- \(|\Delta p_t| \le \epsilon\): stagnant
- \(\Delta p_t > \epsilon\): deteriorating

### 4.10 Drift (PSI)
\[
PSI=\sum_i (p_i-q_i)\ln\frac{p_i}{q_i}
\]

---

## 5) Teknoloji ve Kutuphane Standardi

Zorunlu teknoloji seti:
1. Python 3.11
2. pandas, numpy
3. scikit-learn
4. xgboost
5. shap
6. dice-ml
7. matplotlib
8. pydantic v2
9. pyyaml
10. sqlalchemy + sqlite
11. apscheduler
12. streamlit
13. pytest
14. joblib

Opsiyonel ama onerilen ekler:
1. fairlearn (fairness metrikleri icin)
2. evidently veya alibi-detect (monitoring katmani icin)
3. dowhy/causal-learn adapter (causal dogrulama guclendirmesi icin)

---

## 6) Haftalik Plan - Uctan Uca Teknik Akis

## HAFTA 1 - Iskelet, Konfig, Feature Lock, Schema, DB

Durum: `Tamamlandi (ilk kod parcasi mevcut)`

Hedef:
1. Proje iskeletini ayaga kaldirmak.
2. Veri kontratini ve state store'u kurmak.
3. Dry-run ile temel saglik kontrolu vermek.

Algoritma/Metod:
1. Pydantic veri kontratlari.
2. SQLAlchemy ORM state modeli.
3. Action space coverage kontrolu.
4. Fail-fast feature lock kontrolu.

Matematik:
1. Matematiksel agirlik dusuk, mimari altyapi odakli.
2. \(x_t\), \(z_t\), plan kaydi semantik ayrimi.

Teknoloji:
1. Pydantic v2
2. SQLAlchemy + SQLite
3. Pytest

Adimlar:
1. `configs/features_48.yaml` sozlesmesini yukle.
2. `schema.py` ile data contract siniflarini dogrula.
3. `storage/db.py`, `storage/models.py`, `storage/repository.py` ile DB akislarini kur.
4. `run_train.py --dry_run` ile import/config/db/action-space kontrollerini calistir.

Cikti:
1. Basarili dry-run.
2. Gecen test seti.
3. Run artifact klasoru.

Acceptance:
1. Dry-run hata vermemeli.
2. Feature lock kontrolu aktif olmali.
3. Testler yesil olmali.

---

## HAFTA 2 - Ingest, Preprocess, Split, Processed Veri

Hedef:
1. Raw LendingClub verisini sisteme almak.
2. Feature lock ile uyumlu train/test parquet uretmek.
3. Veri kalitesi raporu vermek.

Algoritma/Metod:
1. Sema denetimi (missing/extra kolon).
2. Tip duzeltme.
3. Missing value politikasi.
4. Encode/transform.
5. Out-of-time split (onerilen) veya stratified split (yedek).

Matematik:
1. Sinif dengesizligi izleme:
\[
\pi_1=\frac{N_{default}}{N_{total}}
\]
2. Train-test dagilim kaymasi:
\[
\Delta \mu_j = |\mu_j^{train}-\mu_j^{test}|
\]

Teknoloji:
1. pandas
2. scikit-learn preprocess bilesenleri
3. pyarrow/parquet

Adimlar:
1. Raw dosyayi yukle.
2. Feature contract'e gore kolon secimi yap.
3. Eksik feature varsa `hard fail`.
4. Fazla feature varsa drop et.
5. Target map islemini deterministic yap.
6. Encode/scale kurallarini kaydet.
7. Train/test split indexlerini versiyonla.
8. `data/processed/train.parquet` ve `test.parquet` yaz.

Cikti:
1. Processed parquet seti.
2. Data summary tablo ve hash.

Acceptance:
1. Kolonlar kontratla birebir uyumlu.
2. Leakage kontrolu temiz.
3. Split tekrarlandiginda ayni indexler uretiliyor.

---

## HAFTA 3 - Model Train, Calibration, Registry

Hedef:
1. PD modeli egitmek.
2. Olasilik kalibrasyonu yapmak.
3. Registry kaydi olusturmak.

Algoritma/Metod:
1. XGBoost binary logistic.
2. Calibration: Isotonic veya Platt (sigmoid).
3. Threshold tabanli karar.

Matematik:
1. Cross-entropy kaybi:
\[
\mathcal{L}=-\frac{1}{N}\sum_i y_i\log\hat{p}_i+(1-y_i)\log(1-\hat{p}_i)
\]
2. Brier score:
\[
BS=\frac{1}{N}\sum_i(\hat{p}_i-y_i)^2
\]
3. ECE:
\[
ECE=\sum_{m=1}^{M}\frac{|B_m|}{N}\left|\text{acc}(B_m)-\text{conf}(B_m)\right|
\]

Teknoloji:
1. xgboost
2. sklearn calibration
3. joblib

Adimlar:
1. Parametreleri `configs/model.yaml`dan oku.
2. Egitim setiyle modeli fit et.
3. Calibration uygula.
4. AUC, PR-AUC, F1, Brier, ECE hesapla.
5. Model ve calibrator artefaktlarini kaydet.
6. `ModelRunRecord` ile registry'ye yaz.

Cikti:
1. `model.joblib`, `calibrator.joblib`
2. `metrics.json`
3. ROC ve calibration curve

Acceptance:
1. Metrikler kayitli.
2. Model versiyonu belirli.
3. Reproducible run snapshot var.

---

## HAFTA 4 - SHAP Global ve Local Aciklama

Hedef:
1. Model davranisini global ve musteri bazli aciklamak.
2. Recourse icin aday feature havuzu cikarmak.

Algoritma/Metod:
1. TreeSHAP global importance.
2. Local SHAP top-k reason extraction.

Matematik:
1. SHAP dekompozisyonu:
\[
f(x)=\phi_0+\sum_{j=1}^{d}\phi_j
\]

Teknoloji:
1. shap
2. matplotlib

Adimlar:
1. Model explainer olustur.
2. Global SHAP ortalama mutlak degerlerini hesapla.
3. Local musteri icin top-k etkili feature cikar.
4. Sebep kodu formatina cevir (customer-facing).

Cikti:
1. Global SHAP tablo + fig
2. Local reason listesi

Acceptance:
1. SHAP ciktilari run bazinda kayitli.
2. Recourse modulu top-k adaylari bu ciktilardan aliyor.

---

## HAFTA 5 - Causal Graph, Action Constraints, Causal Penalty

Hedef:
1. Ozellikler arasi nedensel yapinin yaklasik DAG modelini uretmek.
2. Aksiyonlari DAG ile tutarlilik acisindan puanlamak.

Algoritma/Metod:
1. PC algorithm (MVP default).
2. NOTEARS/ReX adapter (opsiyonel backend).
3. Parent-child baglarina gore ceza fonksiyonu.

Matematik:
1. Ceza:
\[
CausalPenalty(A;G)=\sum_{a \in A}\mathbb{1}[\text{causal violation}(a,G)] \cdot \gamma_a
\]

Teknoloji:
1. causal discovery kutuphaneleri (adapter deseninde)
2. JSON graph export

Adimlar:
1. Causal config'i yukle.
2. Graph discovery calistir.
3. Graph'i `causal_graph.json` olarak kaydet.
4. `graph_utils` ile parent/child query fonksiyonlari yaz.
5. `action_constraints` ile ceza kurallari tanimla.

Cikti:
1. DAG dosyasi
2. Causal penalty fonksiyon ciktilari

Acceptance:
1. Graph olusmali ve parse edilebilir olmali.
2. Recourse scoring bu cezayi kullanmali.

---

## HAFTA 6 - Recourse Generator (Beam Search) ve 9 Plan

Hedef:
1. Her musteri icin 3 ufuk x 3 strateji = 9 plan uretmek.
2. Maliyet, zaman, nedensellik ve risk iyilesmesini birlikte optimize etmek.

Algoritma/Metod:
1. Local SHAP top-k \(\cap\) actionable feature secimi.
2. Beam search candidate expansion.
3. Strategy/horizon bazli plan varyantlari.

Matematik:
1. Toplam plan skoru:
\[
Score = w_1\cdot RiskGain - w_2\cdot Cost - w_3\cdot Time - w_4\cdot CausalPenalty
\]

Teknoloji:
1. Python custom search
2. pydantic plan seyalari

Adimlar:
1. Musteri local SHAP top-k al.
2. Action space'ten izinli featurelari sec.
3. Beam search ile aday planlari genislet.
4. Her plan icin \(x'\), maliyet ve tahmini risk hesapla.
5. Horizon/strategy kombinasyonlarina dagit.
6. 9 plani DB/artifact'a kaydet.

Cikti:
1. Plan JSON/CSV
2. Plan metrik tablosu

Acceptance:
1. Her musteri icin 9 plan var.
2. Planlar deterministic id uretiyor.

---

## HAFTA 7 - Safety Validator (Feasibility + Bootstrap CI)

Hedef:
1. Uretilen planlari iki asamali guvenlik filtresinden gecirmek.

Algoritma/Metod:
1. Feasibility gate:
   - actionable mi
   - direction dogru mu
   - min/max sinirlari asiyor mu
   - adim boyutu uygun mu
2. Statistical gate:
   - Bootstrap CI
   - \(CI_{high} \le \tau_t\) kabul kurali

Matematik:
1. Bootstrap:
\[
p_b(x')=f_b(x',z_t),\quad b=1..B
\]
2. Risk margin:
\[
risk\_margin = \tau_t - CI_{high}
\]

Teknoloji:
1. numpy/pandas bootstrap
2. safety modul paketi

Adimlar:
1. Her plan icin feasibility sonucunu cikar.
2. Feasible planlar icin bootstrap CI hesapla.
3. Status mapping uygula: APPROVED / NEEDS_REVIEW / REJECTED.
4. Gerekce kodu uret.

Cikti:
1. `ci_low`, `ci_high`, `alpha_used`, `risk_margin`, `status`

Acceptance:
1. Her plan icin tekil, acik status var.
2. Status belirleme deterministic.

---

## HAFTA 8 - Macro Stress, Event Impact, Shock Reliability

Hedef:
1. Makro kosullara duyarli threshold ve alpha mekanigi kurmak.
2. Sok senaryolarina karsi plan dayanikliligini olcmek.

Algoritma/Metod:
1. Macro stress index (MSI)
2. Event impact (threshold shift + alpha tightening)
3. Shock scenario simulation
4. Reliability olcumu

Matematik:
1. MSI:
\[
MSI_t=\sum_j w_j \cdot \tilde{z}_{j,t}
\]
2. Threshold shift:
\[
\tau_t = \tau_0 + \delta(MSI_t, event_t)
\]

Teknoloji:
1. macro modulu
2. yaml scenario tanimlari

Adimlar:
1. Macro snapshot yukle.
2. MSI hesapla.
3. Dinamik alpha sec.
4. Sok senaryolarini tek tek uygula.
5. Her plan icin reliability skoru cikar.

Cikti:
1. MSI raporu
2. Scenario-bazli pass/fail tablosu
3. Reliability histogram

Acceptance:
1. Dinamik alpha aktif.
2. Reliability metrikleri plan kaydina islenmis.

---

## HAFTA 9 - Benchmark (Our vs DiCE), Evaluation, Fairness

Hedef:
1. Kendi yaklasiminin baseline'a gore farkini olcmek.
2. Fairness risklerini olcebilir hale getirmek.

Algoritma/Metod:
1. DiCE baseline recourse.
2. Karsilastirma metrikleri:
   - validity
   - proximity
   - sparsity
   - financial cost
   - safe-rate
3. Group fairness:
   - approval gap
   - cost gap

Matematik:
1. Validity:
\[
Validity=\frac{1}{N}\sum_i\mathbf{1}[f(x'_i)\le\tau]
\]
2. Proximity:
\[
Proximity=\frac{1}{N}\sum_i \|x'_i-x_i\|_1
\]
3. Approval gap:
\[
Gap_{approval}=|P(\hat{y}=1\mid g=a)-P(\hat{y}=1\mid g=b)|
\]

Teknoloji:
1. dice-ml
2. evaluation modulu
3. (onerilen) fairlearn

Adimlar:
1. Ayni musteri setinde iki yontemi kos.
2. Metrikleri tek tabloda topla.
3. Fairness raporunu grup bazinda uret.
4. Frontier grafigini olustur.

Cikti:
1. Benchmark tablolari
2. Fairness raporu
3. Karsilastirmali figler

Acceptance:
1. Our vs DiCE sonuc tablosu var.
2. Fairness gap esiklerine gore yorum uretilmis.

---

## HAFTA 10 - Weekly Coaching Loop (Dinamik Kontrol ve Replan)

Hedef:
1. Tek seferlik statik plan yerine haftalik dinamik takip sistemi kurmak.
2. Replan tetikleyicilerini otomatiklestirmek.

Algoritma/Metod:
1. Sequential recourse loop.
2. Progress state machine: improving/stagnant/deteriorating.
3. Replan triggers:
   - deteriorating
   - \(CI_{high} > \tau_t\)
   - aksiyon uyum dusuklugu

Matematik:
1. Haftalik degisim:
\[
\Delta p_t = p_t - p_{t-1}
\]
2. Replan kurali:
\[
\text{replan}_t = \mathbf{1}[\Delta p_t>\epsilon \lor CI_{high,t}>\tau_t \lor compliance_t<c_{min}]
\]

Teknoloji:
1. apscheduler (demo veya simule)
2. coaching modulu

Adimlar:
1. Haftalik snapshot al.
2. Risk ve CI'yi yeniden hesapla.
3. Progress label uret.
4. Trigger varsa yeni plan ureterek eski plani supersede et.
5. Mesajlasma katmaninda reason code goster.

Cikti:
1. 4 haftalik demo loop kaydi
2. Replan olay loglari

Acceptance:
1. En az bir dynamic review ve bir replan senaryosu calisiyor.
2. Statik planin haftalik guncelleme ile degistigi kanitlaniyor.

---

## HAFTA 11 - Retraining Governance, Monitoring, Streamlit UI

Hedef:
1. Champion-challenger yonetimi ile guvenli model guncelleme.
2. Drift + calibration + fairness + recourse KPI birlesik izleme.
3. Offline demo UI.

Algoritma/Metod:
1. PSI drift olcumu.
2. Challenger train + governance gate.
3. PASS/FAIL deployment karari.

Matematik:
1. Governance gate ornegi:
\[
Deploy = \mathbf{1}[AUC_{new}\ge AUC_{min} \land ECE_{new}\le ECE_{max} \land Gap_{fair}\le g_{max} \land Rel_{new}\ge r_{min}]
\]

Teknoloji:
1. retraining modulu
2. monitoring metrikleri
3. streamlit

Adimlar:
1. Drift tetikleyicisini calistir.
2. Challenger modeli egit.
3. Champion ile karsilastir.
4. Governance raporu uret.
5. Streamlit ekranlarina metrik ve plan ciktilarini bagla.

Cikti:
1. Governance PASS/FAIL raporu
2. Drift ve KPI panosu
3. Calisan demo UI

Acceptance:
1. Rollback kosullari tanimli.
2. PASS almayan model deploy edilmiyor.

---

## HAFTA 12 - Final Thesis Pack, Freeze, Sunum Hazirligi

Hedef:
1. Tum sonuclarin final paketini olusturmak.
2. Tez ve demo teslimini stabil hale getirmek.

Algoritma/Metod:
1. Batch run (1000+ sample)
2. Son metrik paketleme
3. Freeze ve smoke test

Matematik:
1. Tablolarda tum ana metriklerin ozet istatistikleri:
\[
\mu,\ \sigma,\ Q_{25},\ Q_{50},\ Q_{75}
\]

Teknoloji:
1. artifacts pack scripts
2. pytest + smoke test komutlari

Adimlar:
1. Tum CLI komutlarini final config ile calistir.
2. Tablolari ve figleri tez klasorune paketle.
3. Reproducibility bilgilerini ekle (seed, config hash, model hash).
4. UI ve CLI smoke test yap.
5. Freeze etiketi olustur.

Cikti:
1. Final thesis pack
2. Demo calistirma kilavuzu
3. Test raporu

Acceptance:
1. Tum zorunlu deliverablelar mevcut.
2. Tek komutla demo ayaga kalkiyor.

---

## 7) Her Hafta Icin Zorunlu Artifact Sozlesmesi

Her run klasoru sunlari icermelidir:
1. `config_snapshot.yaml`
2. `metrics.json`
3. `tables/*.csv`
4. `figures/*.png`
5. `logs.txt`

Opsiyonel ama onerilen:
1. `governance_decision.json`
2. `data_hash.json`
3. `model_card.md`

---

## 8) Ajan Isletim Protokolu

## 8.1 Kod yazmadan once
1. Config dosyalarini oku.
2. Feature contract'i dogrula.
3. Bu dokumanda ilgili haftanin acceptance kriterlerini kontrol et.

## 8.2 Kod yazarken
1. Moduller arasi sorumluluk sinirini bozma.
2. Hard-code parametre ekleme.
3. Her kritik adimda log birak.

## 8.3 Koddan sonra
1. Ilgili CLI komutunu kos.
2. Ilgili pytest paketini kos.
3. Artifact sozlesmesini dogrula.
4. Kisa degisiklik ozeti + risk notu yaz.

---

## 9) Kirmizi Cizgiler (Dokuman Disina Cikma Kurali)

Asagidakiler tez doneminde yasaktir:
1. Bu dokumanda olmayan yeni ana mimari degisiklikler.
2. Feature lock disi gizli feature kullanimi.
3. Tek metrikle model basarisi iddiasi (sadece accuracy gibi).
4. Feasibility veya CI gate'i bypass ederek plan APPROVED etme.
5. Haftalik loop'u statik plana indirgeme.

Asagidakiler zorunludur:
1. Dinamik kontrol ve replan mekanizmasi.
2. Model, fairness, reliability, calibration ve drift metriklerinin birlikte raporlanmasi.
3. Tum kritik kararlarin audit izi.

---

## 10) Devirde Tek Sayfalik Handover Checklist

1. Hangi haftada olundugu net mi.
2. O haftanin girdi dosyalari hazir mi.
3. O haftanin komutu calisiyor mu.
4. O haftanin testleri yesil mi.
5. O haftanin artifact'i tam mi.
6. Bir sonraki haftaya aktarilacak teknik borclar listelendi mi.

---

## 11) Notlar ve Uygulama Tavsiyesi

1. Mevcut kod tabaninda feature kontrati `47 feature + target` olarak calisiyor; dokumanda `48 feature` terminolojisi gecen yerlerde bu fark proje basinda tek seferde normalize edilmelidir.
2. Causal graph sonrasi statik kontrol, yalnizca ara asama kabul edilir; kalici tasarim haftalik dinamik review/replan olmalidir.
3. Bootstrap CI guvenlikte guclu temel sunar; zaman serisi backtest ile birlikte yorumlanmalidir.
4. Tezde metodolojik acikligi korumak icin her deneyi config snapshot ile birlikte kaydetmek zorunludur.

---

## 12) Son Hukum

Bu dokuman:
1. Credit Coach projesinin 12 haftalik teknik anayasa metnidir.
2. Ajan devrinde birincil ve baglayici kaynaktir.
3. Bu metin disina cikilmasi, kapsam kaymasi olarak kabul edilir.
