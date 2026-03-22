# Credit Coach Proje Rehberi

Bu dokumanin amaci, Credit Coach projesini teknik olmayan bir gozle de takip edebilmeni saglamak.

Burada su sorulara cevap veriyorum:

- Bu proje tam olarak ne yapiyor?
- Hangi modeller kullaniliyor?
- Hangi algoritmalar var ve bunlar ne anlama geliyor?
- Proje zaman icinde nasil gelisti?
- Kod tarafinda hangi klasor ne ise yariyor?
- Ciktilari incelerken nereye bakmak gerekir?

Bu dokumani "repo'ya yeni katilan biri icin kisa ama tam bir yol haritasi" gibi dusunebilirsin.

---

## 1. Bu proje ne yapiyor?

Credit Coach, kredi basvurusu su an uygun gorunmeyen bir musteri icin:

1. once risk tahmini yapiyor,
2. sonra "bu musteri ne yaparsa daha iyi gorunur?" sorusuna cevap ariyor,
3. sonra bu onerilerin gercek hayatta yapilabilir olup olmadigini kontrol ediyor,
4. sonra bu onerileri sade bir urun diliyle anlatiyor,
5. sonra butun portfoy uzerinde "bu sistem gercekten ise yariyor mu?" diye olcuyor.

Kisa haliyle:

`risk tahmini + yapilabilir aksiyon plani + urun anlatisi + portfoy kaniti`

Bu proje sadece "puan tahmin eden bir model" degil.
Bir karar destek sistemi.

---

## 2. Projenin buyuk resmi

Projeyi en rahat su sekilde dusunebilirsin:

### Katman 1: Risk motoru

Sistem once musteri verisinden bir risk tahmini uretir.

Buradaki temel soru:

"Bu musteri su an krediyi geri odeme konusunda ne kadar riskli?"

Burada sikca gorecegin kelime:

- **PD (Probability of Default)**: Temerrut olasiligi.
  Basit anlatimla, "geri odeyememe riski" demek.

### Katman 2: Aksiyon plani

Sonra sistem sunu sorar:

"Bu kisinin daha iyi gorunmesi icin hangi degisiklikler anlamli olabilir?"

Eskiden bu tip sistemler daha cok ham degisken diliyle konusur:

- `dti 31 -> 24`
- `revol_util 68 -> 45`

Bu proje artik bunu daha insan diliyle kuruyor:

- harcama baskisini azalt
- kredi karti kullanimini dusur
- odeme duzenini guclendir
- kurum destegi varsa uygun bir teklif kullan

### Katman 3: Gercekcilik kontrolu

Sistem sadece "matematiksel olarak iyi gorunen" plani vermiyor.
Ayni zamanda soruyor:

- Bu hedef gercekci mi?
- Cok mu agresif?
- Yapilmasi cok mu zor?
- Kurum onayi gerekiyor mu?
- Plan kagit ustunde iyi ama gercekte zor mu?

### Katman 4: Anlatim ve urun yuzeyi

Sonra bu teknik ciktilar:

- yoneticinin anlayacagi,
- analistin inceleyebilecegi,
- demo ekraninda gosterilebilecek

bir dille anlatiliyor.

### Katman 5: Portfoy kaniti

En sonda tek bir musteriye bakmakla yetinmiyor.
Toplu halde sunu olcuyor:

- Bu sistem 100 musteri icin nasil davraniyor?
- Cok mu zor planlar oneriyor?
- Gerceklesme ihtimali dusuk mu?
- Kurum destegi nerede kritik hale geliyor?
- Sonuc umut verici mi, yoksa fazla iyimser mi?

---

## 3. Uctan uca akis: Sistem nasil calisiyor?

Bu bolum, projeyi en basit diliyle basa sarip sonuna kadar anlatiyor.

### Adim 1: Veri hazirlaniyor

Kaynak veri temizleniyor, secilen alanlar kilitleniyor ve egitim/test dosyalari uretiliyor.

Onemli nokta:

- Sistem "hangi kolonlari kullanacagim?" konusunu serbest birakmiyor.
- `48 feature` kilidi var.

Buradaki **feature** kelimesi, modelin baktigi bilgi alani demek.
Ornek:

- gelir
- borc orani
- kredi karti kullanim orani
- gecikme bilgileri

Yani feature = modele giren veri kolonu.

### Adim 2: Risk modeli egitiliyor

Sistem gecmis veriden ogrenerek bir tahmin modeli kuruyor.

Bu modelin ana isi:

"Bu musteri krediye cikarsa riski nedir?"

### Adim 3: Olasiliklar duzeltiliyor

Modelin ciktigi olasilik her zaman tam guvenilir olmayabilir.
Bu yuzden ikinci bir duzeltme katmani kullaniliyor.

Buradaki teknik kelime:

- **Calibration**: Modelin verdigi olasiliklari gercege daha uyumlu hale getirme islemi.

Basit anlatim:

Model "%80 risk" dediyse, gercekte de buna yakin bir davranis gormek isteriz.
Kalibrasyon bunu duzeltmeye yardim eder.

### Adim 4: Karar esigi uygulanir

Sistem sadece risk sayisini uretmez.
Bir de su karari verir:

"Bu musteri simdilik kabul bandinda mi, degil mi?"

Buradaki teknik kelime:

- **Threshold / Tau**: Kesme noktasi.

Basit anlatim:

Bir cizgi dusun.
Risk bu cizginin altindaysa daha rahat, ustundeyse daha sorunlu.

### Adim 5: Recourse uretilir

Buradaki en onemli teknik kelime:

- **Recourse**: Bir musterinin sonucunu iyilestirmek icin onerilen aksiyon plani.

Basit anlatim:

"Red alan biri ne yaparsa daha iyi hale gelir?"

Sistem birden fazla aday plan uretir.
Bunlar daha sonra karsilastirilir.

### Adim 6: Planin gercekçiligi kontrol edilir

Sistem artik sadece hedef vermiyor.
Hedefi sunlardan geciriyor:

- yapilabilir mi?
- cok mu buyuk degisim istiyor?
- yonu bozuldu mu?
- anlami kayboldu mu?
- kurum onayi gerekiyor mu?

### Adim 7: Planin zorlugu ve gerceklesme ihtimali hesaplanir

Bu katman sunu soruyor:

"Bu plan kagit ustunde mumkun ama insan bunu gercekte yapar mi?"

Yani:

- mumkun olmak baska,
- uygulamak baska.

### Adim 8: Kurum destegi varsa offer katmani eklenir

Sadece musteri aksiyonu degil, kurumun saglayabilecegi destek de ayri ele alinir.

Ornek:

- limit ayarlamasi
- taksitlendirme
- iskonto / settlement teklifi

Buradaki onemli nokta:

Musteri aksiyonu ile kurum teklifi ayni sey degil.
Proje bunu ayri tutuyor.

### Adim 9: Anlati uretilir

Tum bu teknik dogrular daha okunabilir hale getirilir:

- yonetici ozeti
- ne yapilmali
- ne zaman yapilmali
- neden onemli
- ne kadar gercekci
- kurum ne destek verebilir

### Adim 10: Website ve demo yuzeyine tasinir

Website kendi kafasina gore yeni anlam uretmez.
Python motorunun urettigi tipli artifact'leri kullanir.

Buradaki teknik kelime:

- **Artifact**: Bir calistirmanin sonunda olusan cikti dosyalari.

Ornek:

- JSON
- CSV
- ozet raporlar

### Adim 11: Portfoy ve pilot incelemesi yapilir

Tek musteriyle yetinilmez.
Toplu halde:

- 50 musteri
- 100 musteri
- tum test portfoyu

uzerinde inceleme yapilir.

Bu sayede sistemin:

- sadece tek bir ornekte guzel gorunup gorunmedigi,
- yoksa genel olarak saglam calisip calismadigi

olculur.

---

## 4. Bu projede hangi modeller kullanildi?

Burada cok onemli bir ayrim var:

Bu projede tek bir model yok.

Iki ana sey var:

1. **Gercek ogrenme yapan tahmin modeli**
2. **Kurala dayali karar ve planlama katmanlari**

### 4.1 Ana risk modeli

Ana model tarafinda iki temel secenek var:

- **XGBoost**
- **Logistic Regression**

#### XGBoost nedir?

XGBoost, tablo verisinde cok guclu calisan bir makine ogrenmesi yontemidir.

Basit anlatim:

Bir tek kural yerine,
bir suru kucuk karar agacini bir araya getirir
ve bunlardan daha guclu bir tahmin motoru olusturur.

Bu proje icin ana tercih bu.

Dosya referansi:

- `credit-coach/configs/model.yaml`
- `credit-coach/src/credit_coach/model/train.py`

#### Logistic Regression nedir?

Bu daha klasik ve daha basit bir tahmin modelidir.

Basit anlatim:

Her degiskenin etki yonunu ve buyuklugunu daha sade bir formulle hesaplar.

Bu projede neden var?

- Yedek model olarak
- XGBoost kullanilamazsa sistemin tamamen durmamasi icin

Yani sistem "tek motora bagimli" degil.

### 4.2 Kalibrasyon modeli

Ana modelin ustune bir de kalibrasyon var.

Burada kullanilan yontemler:

- **Isotonic calibration**
- **Sigmoid / Platt scaling**

#### Isotonic ne demek?

Modelin olasiliklarini veri uzerine gore daha gercekci hale getiren bir duzeltme yontemi.

Sade anlatim:

"Modelin yuzdeleri biraz ayara ihtiyac duyuyorsa, bunlari gercege daha yakin hale getiriyoruz."

### 4.3 Guven / belirsizlik katmani

Projede sadece "tek sayi" verilmek istenmiyor.
Bir miktar belirsizlik bilgisi de tutuluyor.

Burada gorecegin kelimeler:

- **Confidence interval**: Guven araligi
- **Conformal calibration**: Belirsizlik bandi uretmek icin kullanilan ek yapi

Sade anlatim:

Sistem sadece "risk = 0.31" demek istemiyor.
Ayni zamanda "bu sayida biraz oynama olabilir" demek istiyor.

### 4.4 Ayrica sunlar kullaniliyor

- **SHAP**: Modelin kararinda hangi degiskenlerin etkili oldugunu aciklamak icin
- **DiCE-ML**: Alternatif aksiyon adaylari uretmek icin

#### SHAP nedir?

Modelin bir kisi icin neden bu karari verdigini anlamaya yardim eden aciklama yontemi.

Basit anlatim:

"Bu kiside riski en cok yukselten seyler hangileri?"

#### DiCE nedir?

Birden fazla alternatif "ne degisse sonuc duzelirdi?" senaryosu ureten arac.

Basit anlatim:

"Sadece tek bir plan degil, alternatif planlar da uretelim."

---

## 5. Hangi algoritmalar var?

Bu proje yalnizca bir tahmin modeli degil.
Asil degeri, modelin ustune kurulan karar mekaniklerinde.

Buradaki "algoritma" kelimesini soyle dusun:

Bir problemin adim adim nasil cozuldugunu anlatan is kurali ya da hesap mantigi.

### 5.1 Recourse search

Sistem bir musteri icin birden fazla aksiyon plani ariyor.

Basit anlatim:

"Hangi degisiklik kombinasyonlari sonucu iyilestirir?"

Bu tarama sirasinda:

- ic mantikla uretilen planlar,
- DiCE'den gelen alternatifler,
- fallback planlar

birlikte degerlendirilebiliyor.

### 5.2 Feasibility engine

Bu katman sunu soruyor:

"Bu hedef mantikli ama uygulanabilir mi?"

Ornek:

- gelir artisi cok buyuk mu?
- kart kullanim dususu asiri mi?
- hedef anlamsiz hale mi geldi?

Buradaki verdict kelimeleri:

- **valid**: uygun
- **clipped**: biraz kirpildi
- **repaired**: duzeltilerek tutuldu
- **provisional**: kosullu
- **invalid**: gecersiz

### 5.3 Execution modeling

Bu katman sunu soruyor:

"Plan mumkun ama insan bunu gercekte ne kadar uygular?"

Burada bakilan seyler:

- maliyet
- sure
- takip yuklu mu
- kurum onayi gerektiriyor mu
- cok fazla adim var mi

### 5.4 Offer optimization

Bu katman kurum tarafini ayri ele aliyor.

Soru su:

"Kurum destek verirse hangi teklif anlamli olur?"

Ornek:

- taksitlendirme
- indirim
- limit ayarlamasi

Burada onay beklemek ile musteri kabulunu beklemek ayri sey olarak ele aliniyor.

### 5.5 Trajectory planning

Sistem tek bir anlik tavsiye vermiyor.
Zaman icinde planin nasil ilerleyecegini de kuruyor.

Temel kontrol noktalar:

- 4 hafta
- 12 hafta
- 24 hafta

Yani proje su soruya da cevap veriyor:

"Bu plan hemen mi etki eder, yoksa orta vadede mi?"

### 5.6 Portfolio validation

Bu katman tek musteri yerine tum kitleye bakiyor.

Sade anlatim:

"Bu sistem genel olarak ne kadar faydali, ne kadar gercekci?"

Burada bakilan seylerden bazilari:

- plan kapsama orani
- gerceklesme agirlikli fayda
- gereksiz iyimserlik var mi
- hangi segmentlerde daha iyi calisiyor

### 5.7 Pilot integration

Bu katman canli banka entegrasyonu degil.

Ama su demek:

"Gercek kurum datasina benzeyen bir paket alip, bunu kontrollu bir sekilde sistemden gecirebiliyoruz."

Yani pilot hazirlik seviyesi var.
Ama tam canli entegrasyon daha sonraki asama.

---

## 6. Teknik kelimeler sozlugu

Bu bolumu kisa bir referans gibi kullanabilirsin.

- **Model**: Veriden ogrenip tahmin yapan yapi.
- **Feature**: Modele giren bilgi alani.
- **PD**: Geri odeyememe riski.
- **Calibration**: Model olasiliklarini gercege yaklastirma.
- **Threshold / Tau**: Karar icin kullanilan kesme noktasi.
- **Recourse**: Sonucu iyilestirmek icin onerilen aksiyon plani.
- **Artifact**: Run sonunda olusan cikti dosyasi.
- **Narrative**: Teknik ciktiyi insan diline ceviren anlatim.
- **Feasibility**: Hedefin gercek hayatta uygulanabilir olmasi.
- **Execution probability**: Planin gercekte uygulanma olasiligi.
- **Offer**: Kurumun saglayabilecegi destek veya teklif.
- **Portfolio**: Tek musteri degil, tum musteri kitlesi.
- **Pilot**: Gercek dunyaya yaklastirilmis kontrollu deneme asamasi.
- **Heuristic**: Tamamen veriden ogrenilmis olmayan, uzman mantigiyla yazilmis kural veya hesap.
- **Fail closed**: Emin olunmayan durumda "gecir" demek yerine "durdur" demek.

---

## 7. Bu projede hangi kisimlar ogrenilmis model, hangi kisimlar kural tabanli?

Bu ayrimi bilmek cok onemli.

### Ogrenilmis / veriyle egitilen kisimlar

- risk tahmin modeli (`XGBoost` veya `Logistic Regression`)
- kalibrasyon katmani
- SHAP aciklama katmani
- DiCE ile alternatif aday arama

### Kural tabanli kisimlar

- aksiyon semantigi
- feasibility karar mantigi
- execution difficulty mantigi
- offer contract mantigi
- checkpoint / trajectory mantigi
- urun anlatisi ve business-vs-technical ayrimi
- portfoy review paketleme
- pilot guardrail mantigi

Bu neden iyi bir sey?

Cunku banka benzeri sistemlerde her seyi tek bir kara kutuya birakmak istemezsin.
Bazi yerlerde ogrenme,
bazi yerlerde acik ve denetlenebilir kural gerekir.

---

## 8. Kod tarafinda hangi klasor ne ise yariyor?

Burasi repo'yu gezerken en faydali kisimlardan biri olacak.

## 8.1 `credit-coach/`

Burasi Python motoru.
Asil hesap ve karar mantigi burada.

### `src/credit_coach/model/`

Risk modelinin egitimi, tahmini, kaydi ve kalibrasyonu burada.

Buraya bak:

- `train.py`
- `predict.py`
- `calibrate.py`
- `registry.py`

### `src/credit_coach/recourse/`

Projenin "aksiyon plani" kalbi burada.

Buraya bak:

- `action_space.py`
- `generator.py`
- `feasibility.py`
- `execution_probability.py`
- `offer_optimization.py`
- `trajectory.py`
- `dice_baseline.py`

### `src/credit_coach/coaching/`

Planin insan diline cevrildigi ve roadmap mantiginin yonetildigi katman.

Buraya bak:

- `messaging.py`
- `planner.py`
- `loop.py`

### `src/credit_coach/evaluation/`

Portfoy seviyesinde dogrulama ve kanit katmani.

Buraya bak:

- `portfolio_validation.py`
- fairness ve benchmark dosyalari

### `src/credit_coach/cli/`

Komut satirindan calisan giris noktalarinin oldugu yer.

En onemlileri:

- `run_prepare_data.py`
- `run_train.py`
- `run_recourse.py`
- `run_batch_recourse_eval.py`
- `run_customer_artifact_collection.py`
- `run_phase_experiment_suite.py`
- `run_pilot_integration.py`
- `run_production_smoke.py`

### `src/credit_coach/causality/`

Nedensellik tarafinin yardimci dosyalari.

Basit anlatim:

"Bir degisken degisti diye her seyin sihirli bicimde duzelmis sayilmamasi" icin kullanilan mantik.

### `src/credit_coach/ops/`

Release gate, KPI, telemetry, smoke test gibi operasyon katmani.

Yani:

"Bu sistemi urune cikaracak olsak nasil kontrollu cikariz?"

### `src/credit_coach/pilot/`

Kurumdan gelen paketlerin normalize edildigi ve pilot akisinin kuruldugu yer.

## 8.2 `credit-coach-website/`

Burasi sunum ve urun yuzeyi.

Onemli prensip:

Website karar vermez.
Website gosteren taraftir.

Yani:

- Python engine = beyin
- website = vitrin / urun yuzeyi

### `client/`

React arayuzu.

### `server/`

Website backend.
Ama agir model mantigi burada degil.

### `shared/`

Frontend ve backend'in ayni veri kontratini kullanmasi icin ortak tipler.

### `demo-data/`

Curated demo snapshot'lari.
Canli model logic burada degil; burada daha cok gosterim icin tutulmus veri var.

## 8.3 `.planning/`

Projenin zaman icindeki gelisim hikayesi burada.

Eger "ne neden yapildi?" sorusuna cevap ariyorsan burasi cok kiymetli.

Ozellikle:

- `PROJECT.md`
- `MILESTONES.md`
- `milestones/`

---

## 9. Proje zaman icinde nasil gelisti?

Bu kisim projeyi zihninde oturtmak icin cok faydali.

### v1.0 - Temel motor kuruldu

Bu asamada proje sunlari kazandi:

- model egitimi
- recourse temeli
- benchmark
- fairness
- telemetry
- release / smoke test mantigi

Yani cekirdek altyapi kuruldu.

### v1.1 - Guvenlik ve KPI sertlesti

Bu asamada sistem sadece "calisiyor mu?" degil,
"kurumsal olarak guvenilir mi?" sorusuna yaklasti.

### v1.2 - Oneri kalitesi guclendi

Bu cok onemli bir donum noktasi.

Burada:

- ham feature degisimleri daha anlamli aksiyonlara dondu
- execution-aware mantik geldi
- zaman icindeki checkpoint dusuncesi guclendi
- offer ve learning loop katmani olgunlasti

### v1.3 - Urunlesme ve portfoy kaniti geldi

Bu asamada:

- demo ve proof yuzeyi ciddilesti
- anlati motorun icine tasindi
- analist ve buyer icin daha okunur hale geldi
- pilot readiness baseline kuruldu

### v2.0 - Personalized Action & Decision Intelligence

Bu milestone projenin bugunku en onemli seviyesini temsil ediyor.

Burada:

- semantik aksiyonlar netlesti
- bu aksiyonlar sayisal hedefe dondu
- sayisal hedefler feasibility filtresinden gecmeye basladi
- zorluk ve takip edilme ihtimali plan kalitesine girdi
- kurum teklifleri ayri bir katman oldu
- anlati daha urun-ready hale geldi
- website typed consumer oldu
- portfoy seviyesinde numeric impact ve calibration review geldi
- pilot package runner eklendi

Kisaca:

Bu milestone ile proje "sadece tavsiye motoru" olmaktan cikti,
"kisisellestirilmis karar zekasi sistemi" haline geldi.

---

## 10. Bugun bu projede en onemli gucler neler?

Benim gordugum en guclu taraflar bunlar:

### 10.1 Tek bir model degil, katmanli sistem

Bu iyi bir sey.
Cunku kredi karari gibi zor alanlarda tek basina model yetmez.

### 10.2 Engine source of truth

Website veya demo kendi anlamini uydurmuyor.
Asil dogru Python motorundan geliyor.

### 10.3 "More honest than impressive" yaklasimi

Bu proje sadece parlatilmis uplift gostermiyor.
Sunlari da gostermeye calisiyor:

- gerceklesme zorlugu
- execution gap
- false optimism
- weak 4w health

Bu urun guveni icin cok onemli.

### 10.4 Pilot-ready dusunulmus

Canli entegrasyon yoksa bile,
kuruma gidecek paket mantigi kurulmus.
Bu, projeyi akademik demo olmaktan cikarip urun yoluna sokuyor.

---

## 11. Hala hangi alanlar acik?

Proje guclu bir seviyede ama tamamlanmis degil.

Acik tasinan ana alanlar:

- dis kurum entegrasyonlari
- regulatory / adverse action explanation pack'leri
- proof refresh ve release review otomasyonu
- kurum tarafli policy / offer sync

Yani sistem artik iyi bir "beyin" ve iyi bir "urun demosu" seviyesinde.
Siradaki buyuk adim daha derin entegrasyon ve operasyonel otomasyon olur.

---

## 12. Ciktilari incelerken nereye bakmali?

Eger tek musteriye bakiyorsan:

- `credit-coach/artifacts/runs/<run_id>/tables/customer_roadmap.json`
- `credit-coach/artifacts/runs/<run_id>/tables/plans.json`
- `credit-coach/artifacts/runs/<run_id>/metrics.json`
- `credit-coach/artifacts/runs/<run_id>/tables/customer_roadmap_steps.csv`

Eger toplu inceleme yapiyorsan:

- `credit-coach/artifacts/runs/<run_id>/tables/customer_artifact_collection/flat/customer_metrics.csv`
- `credit-coach/artifacts/runs/<run_id>/tables/customer_artifact_collection/flat/customer_plans.csv`
- `credit-coach/artifacts/runs/<run_id>/tables/customer_artifact_collection/flat/customer_roadmap_steps.csv`
- `credit-coach/artifacts/runs/<run_id>/tables/customer_artifact_collection/collection_summary.md`

Eger urun / proof tarafina bakiyorsan:

- `credit-coach-website/demo-data/single_customer_roadmap.json`
- `credit-coach-website/demo-data/product_confidence_snapshot.json`

Ama cok kritik not:

Website snapshot'lari her zaman en guncel engine run'i olmayabilir.
Gercek kaynak olarak engine artifact'lerini esas almak daha dogru olur.

---

## 13. Bu projeyi ogrenmek icin en iyi okuma sirasi

Eger sifirdan ogrenmek istiyorsan sana su sirayi oneririm:

1. Bu dokumani oku.
2. `credit-coach/README.md` dosyasini oku.
3. `.planning/PROJECT.md` dosyasini oku.
4. `.planning/MILESTONES.md` dosyasini oku.
5. `credit-coach/src/credit_coach/cli/run_train.py` dosyasini oku.
6. `credit-coach/src/credit_coach/cli/run_recourse.py` dosyasini oku.
7. `credit-coach/src/credit_coach/recourse/` klasorunu gez.
8. `credit-coach/src/credit_coach/coaching/messaging.py` dosyasina bak.
9. `credit-coach/src/credit_coach/evaluation/portfolio_validation.py` dosyasina bak.
10. En son `credit-coach-website/TECH_ARCHITECTURE.md` ile website tarafini oku.

Bu sirayla gidersen once "ne"yi, sonra "nasil"i, sonra "neden"i anlarsin.

---

## 14. Tek cumlede kapanis

Credit Coach, kredi riski tahmin eden bir modelin ustune kurulu; ama asıl degeri, bu tahmini gercek dunyada uygulanabilir aksiyonlara, kurum tekliflerine, urun anlatilarina ve portfoy kanitina ceviren katmanli karar sistemi olmasinda.
