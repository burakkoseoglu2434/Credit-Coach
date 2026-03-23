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

## Cok kisa ozet

- Credit Coach kredi riski tahmini yapar.
- Uygun olmayan musteri icin uygulanabilir aksiyon plani uretir.
- Bu planin gercekciligini ve uygulanma ihtimalini olcer.
- Kurum tekliflerini ayri bir katman olarak degerlendirir.
- Tek musteri ve portfoy duzeyinde karar, kanit ve operator inceleme paketi uretir.
- Business-visible son durumlari net tasir: `APPROVED | CONDITIONAL | REJECTED`.

---

## 1. Bu proje ne yapiyor?

Credit Coach, kredi basvurusu su an uygun gorunmeyen bir musteri icin:

1. once risk tahmini yapiyor,
2. sonra "bu musteri ne yaparsa daha iyi gorunur?" sorusuna cevap ariyor,
3. sonra bu onerilerin gercek hayatta yapilabilir olup olmadigini kontrol ediyor,
4. sonra bu onerileri sade bir urun diliyle anlatiyor,
5. sonra butun portfoy uzerinde "bu sistem gercekten ise yariyor mu?" diye olcuyor.

Kisa haliyle:

`risk tahmini + yapilabilir aksiyon plani + deterministic karar + urun anlatisi + portfoy kaniti`

Bu proje sadece "puan tahmin eden bir model" degil.
Bir karar destek sistemi.

---

## 2. Projenin buyuk resmi

Projeyi en rahat su sekilde dusunebilirsin:

### Model ile engine farki

Bu ayrimi en basindan net tutmak cok faydali:

- **Model** = risk tahmini yapan ogrenilmis parca
- **Engine** = model + recourse + feasibility + execution + kurum teklifi + anlati + validation

Yani model, engine'in sadece bir parcasi.
Projenin asil degeri butun engine katmanlarinda.

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
- kurum teklifi varsa uygun bir destek yolunu kullan

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
- Kurum teklifi nerede kritik hale geliyor?
- Sonuc umut verici mi, yoksa fazla iyimser mi?

### 2.1 Bugun sistem ne uretir?

Bu kisim, bugunku urunun somut olarak ne ciktigini hizlica gormek icin faydali.

#### Tek musteri icin

- deterministic decision summary
- executive summary
- action steps
- checkpoints
- kurum teklifi anlatisi
- technical reveal
- operator packet
- institution-facing explanation pack

#### Portfoy icin

- decision funnel
- readiness dagilimi
- calibration review
- operator briefing
- numeric plan coverage
- requested change burden
- execution-aware payoff
- realization gap
- kurum teklifi destekli realization share

Bu listeyi su sekilde okuyabilirsin:

- tek musteri tarafi = "bu kisi icin ne yapmaliyiz?"
- portfoy tarafi = "bu sistem genel olarak ne kadar faydali ve ne kadar gercekci?"

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

### Adim 8: Kurum teklifi (offer) varsa ayri katman eklenir

Sadece musteri aksiyonu degil, kurumun saglayabilecegi teklif de ayri ele alinir.

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

### Adim 9.1: Final karar sahipligi uygulanir

Bu proje artik sadece plan onermiyor.
Ayni zamanda her musteri icin deterministic bir final karar da tasiyor.

Business-visible karar seti:

- `APPROVED`
- `CONDITIONAL`
- `REJECTED`

Internal tarafta bir de istisna kovasi var:

- `NEEDS_REVIEW`

Ama cok onemli kural:

- bu internal durum dis yuzeye sizmaz
- website ve operator'un kisa yuzeyi sadece 3-state karar gorur

Bu ayrim, sistemi "interesting prototype" olmaktan cikarip
"karar sahibi fintech artefact" seviyesine tasiyan ana adimlardan biridir.

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

### 5.8 Decision ownership ve contract trust

Bu yeni katmanlarin amaci sudur:

- ham output'lari null-free yapmak
- raw ve flat artefact'leri ayni dogruyu tasir hale getirmek
- final karari tek yerde sahiplenmek
- operator ve proof yuzeylerinin ayni karar dilini kullanmasini saglamak

Pratikte bunun anlami:

- `customer_roadmap.json` artik sadece "plan dump" degil
- `summary` bolumu final customer truth'u tasir
- `customer_metrics.csv` ve `customer_plans.csv` bu truth'u mirror eder
- parity bozuksa bu gizlenmez
- ama artefact bug'i musteri karari gibi maskelenmez

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

## 6.1 Teknik ifadeleri biraz daha derin ama sade anlatalim

Bu bolumde ayni kelimeleri bir adim daha aciyorum.
Amacim "tanimini bilmek" degil, "neden var?" sorusunu da netlestirmek.

### Model

Model, gecmis veriye bakip gelecekle ilgili tahmin yapan yapidir.

Bu projede modelin ana gorevi:

"Bu kisinin geri odeyememe riski ne?"

Model, kendi basina tavsiye motoru degildir.
Sadece baslangic noktasi verir.

Yani:

- model = risk tahmini
- proje = risk tahmini + ne yapilabilir + ne kadar gercekci + nasil anlatilir

### XGBoost

XGBoost, tablo verisinde cok guclu calisan bir tahmin yontemidir.

Sade bir benzetme:

Tek bir uzmana sormak yerine,
ayni soruya bakan bir suru kucuk uzmani birlestirip
daha iyi bir karar almak gibi dusunebilirsin.

Bu projede neden kullaniliyor?

- gelisiguzel kurallardan daha guclu tahmin verdigi icin
- tablo verisinde iyi performans gosterdigi icin
- kredi riskinde yaygin kullanilan bir yaklasim oldugu icin

### Logistic Regression

Bu, daha klasik ve daha sade bir modeldir.

Sade benzetme:

Her bilginin risk uzerindeki etkisine bir agirlik verir ve bunlari toplar.

Bu projede neden hala var?

- yedek olarak
- XGBoost devreye giremezse sistemi ayakta tutmak icin
- bazen daha basit ve aciklanabilir bir taban almak icin

### Prediction

Prediction, modelin tahmin uretmesi demek.

Bu projede prediction ciktisi genelde bir risk olasiligi.
Yani kesin "olur/olmaz" degil, bir ihtimal sayisi.

### PD

PD, "Probability of Default" kisaltmasi.

Pratik anlami:

"Bu kisinin geri odeyememe riski"

PD yuksekse risk daha yuksek kabul edilir.
PD dusukse profil daha rahat kabul edilir.

### Threshold / Tau

Threshold, karar verirken kullanilan esiktir.

Basit dusunce:

- PD bu cizginin altinda -> daha rahat
- PD bu cizginin ustunde -> daha riskli

Bu projede bu cizgi sabit bir is karari gibidir.
Yani model tek basina son karari vermez; karar bir esige gore yorumlanir.

### Calibration

Kalibrasyon, modelin verdigi olasiliklari gercege daha yakin hale getirme isidir.

Ornek:

Eger model 100 kisiye "%70 risk" diyorsa,
gercekte de buna yakin bir bozulma davranisi gormek isteriz.

Kalibrasyonun amaci:

"Modelin yuzdeleri sadece siralama olarak degil, anlam olarak da daha dogru olsun."

### Isotonic calibration

Kalibrasyonun bir turu.

Bunu soyle dusun:

Modelin ciktisini tamamen bastan kurmuyor,
ama egriyi biraz duzeltiyor.
Boylece "%20", "%40", "%60" gibi degerler daha mantikli hale geliyor.

### Sigmoid / Platt scaling

Kalibrasyonun baska bir turu.

Isotonic'ten biraz daha sade ve daha kisitli bir duzeltme gibi dusunebilirsin.

Genelde:

- isotonic = daha esnek
- sigmoid = daha sade

### Confidence interval / guven araligi

Sistem bazen tek bir sayi vermek yerine bir belirsizlik bandi da tasir.

Bu neden onemli?

Cunku gercek dunyada "tam olarak 0.3127" gibi bir kesinlik hissi cogu zaman sahte olabilir.

Guven araligi sunu der:

"Bu tahmini ciddiye al, ama milimetre hassasiyetinde mutlak gercek gibi okuma."

### Conformal calibration

Bu, belirsizlik ve guven bandi tarafinda kullanilan ek bir yapi.

Basit anlami:

"Sadece tahmin vermeyelim; ne kadar sasabilecegimizi de olculu sekilde anlatalim."

Bu proje icin neden degerli?

Cunku kredi gibi alanlarda sadece nokta tahmin yeterli degil.
Bir miktar "eminlik seviyesi" de lazim.

### Feature

Feature, modele giren bilgi alani.

Ornek:

- gelir
- borc orani
- kredi karti kullanimi
- gecikme bilgisi

Bu projede 48 feature kilidi olmasi ne demek?

Sistem "bugun su kolonlari kullandim, yarin baska kolonlari" gibi kaygan davranmiyor.
Bu, tekrar edilebilirlik ve denetim icin onemli.

### Feature engineering

Ham veriyi modelin kullanabilecegi hale getirme isidir.

Ornek:

- eksik deger doldurma
- kategorik alanlari sayisal hale getirme
- train/test dosyasi hazirlama

Bu proje bu isi de kontrollu yapiyor.

### Recourse

Bu projenin merkez kelimelerinden biri.

Recourse demek:

"Bir kisinin sonucunu iyilestirmek icin ne yapabilecegini hesaplayan plan"

Yani:

- sadece risk tahmini degil
- riski nasil dusurebilecegine dair yol haritasi

### Action semantics

Bu ifade biraz teknik ama cok onemli.

Anlami:

Ham veri degisimini, gercek hayatta anlasilabilir aksiyona cevirmek.

Ornek:

- ham veri dili: `revol_util 68 -> 45`
- action semantics dili: "kredi karti kullanimini dusur"

Bu neden kritik?

Cunku kullaniciya ham feature adi gostermek urun dili acisindan zayif kalir.

### Numeric target

Sadece "kullanimi dusur" demek yetmez.
Ne kadar dusurmesi gerektigini de soylemek gerekir.

Iste numeric target bunun icin var.

Ornek:

- mevcut: `%68`
- hedef: `%45`
- delta: `-23 puan`

### Feasibility

Bir hedefin gercekten uygulanabilir olup olmadigini kontrol eden katman.

Ornek:

- gelir bir ayda 3 kat artsin -> muhtemelen gercekci degil
- kart kullanimini makul seviyede azalt -> olabilir

Yani feasibility, "iyi gorunuyor" ile "yapilabilir" arasindaki farki korur.

### Constraint

Constraint, sinir veya kisit demek.

Bu projede constraint su tip sorulari temsil eder:

- sistem buna izin veriyor mu?
- is kurali buna izin veriyor mu?
- gercek hayat buna izin veriyor mu?
- baska bir aksiyonla cakisiyor mu?

### Clipped / repaired / invalid

Bu kelimeler feasibility tarafinda sik gorulur.

- **clipped**: Hedef biraz fazla agresifti, makul seviyeye kirpildi
- **repaired**: Plan tamamen cope atilmadi, duzeltilerek tutuldu
- **invalid**: Bu plan artik anlamli degil, elenmeli

Bu ayrim neden degerli?

Cunku sistem her problemi tek tepkiyle cozmuyor.
Bazen duzeltmek yeterli, bazen tamamen vazgecmek gerekir.

### Execution probability

Bu, planin gercekte uygulanma ihtimali.

Burada odak su:

"Bu plan kagit ustunde iyi, ama insan gercekte bunu yapar mi?"

Bu proje icin cok kritik.
Cunku sadece nominal iyilesme yetmiyor.
Gerceklesme sansi da gerekiyor.

### Difficulty

Difficulty, planin zorluk seviyesi.

Burada sistem su faktorleri dusunuyor:

- maliyet
- sure
- cok adim var mi
- koordinasyon gerekiyor mu
- kurum onayi gerekiyor mu

Yani:

- feasibility = mumkun mu?
- difficulty = yapmak ne kadar zor?

### Heuristic

Heuristic, tamamen makine ogrenmesiyle egitilmis olmayan, uzman mantigiyla yazilan pratik kural demek.

Bu proje sadece ogrenilmis model kullanmiyor.
Bazi katmanlarda heuristic kullanmak daha dogru.

Neden?

Cunku her seyi kara kutu yapmak istemiyoruz.
Bazi yerlerde denetlenebilir is kurali lazim.

### SHAP

SHAP, modelin neden o sonucu verdigini anlamaya yardim eden aciklama teknigi.

Basit anlatim:

"Bu kiside riski en cok yukari ceken seyler neler?"

Bu neden onemli?

Cunku kredi tarafinda sadece skor yetmez.
Bir miktar neden bilgisi de lazim.

### DiCE

DiCE, alternatif counterfactual planlar ureten bir arac.

Counterfactual'i sade anlatimla soyle dusun:

"Bu kisi icin hangi farkli degisiklik kombinasyonlari sonucu iyilestirebilir?"

Yani DiCE, sisteme sadece tek bir yol degil, alternatif yollar da dusunme imkani verir.

### Counterfactual

Gercekte yasanmamis ama "eger boyle olsaydi" diye kurulan alternatif senaryo.

Ornek:

"Geliri biraz daha yuksek, kart kullanimi biraz daha dusuk olsaydi ne olurdu?"

### Trajectory

Trajectory, planin zaman icindeki yolculugu demek.

Bu proje "bir gunluk tavsiye" vermek yerine su soruyu soruyor:

- 4 haftada ne olur?
- 12 haftada ne olur?
- 24 haftada ne olur?

Yani planin zamana yayilan etkisini izliyor.

### Checkpoint

Checkpoint, kontrol noktasi.

Bu projede sabit kontrol noktalar var:

- 4 hafta
- 12 hafta
- 24 hafta

Bu noktalar, planin gidisatini izlemek icin kullaniliyor.

### Kurum teklifi (offer)

Offer, yani kurum teklifi, kurum tarafindan saglanabilecek destek veya teklif.

Bu neden ayri katman?

Cunku musteri aksiyonu ile kurum teklifi ayni sey degil.

Ornek:

- musteri harcamayi azaltir
- kurum taksitlendirme sunar

Ikisi birlikte bir plan olabilir, ama ayni kavram degil.

### Approval ve acceptance

Bu ikisi karisir, ama farki onemli:

- **approval**: kurum bu teklifi veriyor mu?
- **acceptance**: musteri verilen teklifi kabul ediyor mu?

Yani:

- supply-side gate = kurum tarafi
- customer-side realization = musteri tarafi

### Urun anlatisi (narrative)

Narrative, yani urun anlatisi, teknik ciktinin urun diline cevrilmis hali.

Bu projede urun anlatisi neden engine tarafinda?

Cunku website kendi basina yorum uretmesin isteniyor.
Anlatim da hesap mantigi kadar kontrollu olsun isteniyor.

### Typed contract / schema

Bu ifade su anlama gelir:

"Veri su sekilde gelmeli; alanlari, tipi ve anlami belli olmali."

Bu neden onemli?

Cunku:

- backend baska
- frontend baska
- artifact dosyalari baska

olsa da herkes ayni dili konussun isteriz.

### Artifact

Artifact, run sonunda disari yazilan cikti dosyasi.

Bu proje artifact-first yaklasim kullanir.

Anlami:

"Asil dogruyu kodun icinde gizlemek yerine, izlenebilir dosyalar halinde ciktiya yaz."

Bu denetim acisindan cok gucludur.

### Registry

Registry, egitilen modelin kaydedildigi yer.

Yani:

- hangi model kullanildi
- hangi versiyon
- hangi kalibrasyon dosyasi

gibi bilgilerin tutuldugu klasor mantigi.

### Batch run

Batch, tek musteri degil bir topluluk uzerinde calisma demek.

Ornek:

- 100 musteri icin ayni pipeline'i calistirmak

Bu proje icin batch cok onemli.
Cunku tek ornek guzel olabilir ama portfoy gercegi farkli olabilir.

### Portfolio validation

Portfoy seviyesinde sistemin ne kadar iyi, ne kadar gercekci ve ne kadar durust davrandigini kontrol eden katman.

Yani:

"Bu proje genel olarak ise yariyor mu?"

### Calibration review

Bu, sistemin fazla iyimser olup olmadigini kontrol eden inceleme katmani.

Basit anlatim:

"Sistem guzel konusuyor ama gercekte biraz fazla mi umut satiyor?"

Bu projenin one cikan guclerinden biri, bu soruyu ciddi almasi.

### Fairness

Fairness, sistemin farkli gruplara adil davranip davranmadigini inceleyen alan.

Basit anlatim:

"Bu sistem bir gruba gereksiz sert, baska bir gruba gereksiz yumusak mi?"

### Benchmark

Benchmark, farkli model veya surumleri karsilastirma duzeni.

Yani:

"Yeni yapi eskisinden daha iyi mi?"

### Challenger model

Challenger, mevcut modele meydan okuyan alternatif model veya ayar seti.

Bu neden onemli?

Cunku mevcut sistemin daha iyi oldugunu varsaymak yerine, test etmek gerekir.

### Telemetry

Telemetry, sistem calisirken olusan teknik ve operasyonel sinyalleri toplama isi.

Basit anlatim:

"Sistem sahada nasil davraniyor, nerede sorun cikiyor?"

### Smoke test

Smoke test, buyuk sisteme girmeden once yapilan hizli saglik kontrolu.

Sade anlatim:

"En temel seyler ayakta mi?"

### Guardrail

Guardrail, sistemi raydan cikarmamasi icin konulan koruyucu sinir.

Ornek:

- fairness bozulduysa cikma
- KPI dusukse rollout yapma
- riskli artefact varsa pilot'a izin verme

### Pilot integration

Pilot integration, gercek kuruma yakin veri paketleriyle kontrollu calisma yapabilmek demek.

Bu, tam canli entegrasyonla ayni sey degil.

Ama su demek:

"Bu sistemi kurumsal ortama yaklastiracak format ve guardrail mantigi artik var."

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
- kurum teklifi contract mantigi
- checkpoint / trajectory mantigi
- final decision ownership
- raw/flat parity ve contract sagligi
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

### `src/credit_coach/decision/`

Final karar sahipligi burada yasar.

Buraya bak:

- `ownership.py`

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
- `run_pilot_baseline_refresh.py`
- `run_pilot_artifact_qa.py`
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
- kurum teklifi ve learning loop katmani olgunlasti

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

### v2.1 - Decision Ownership & Pilot-Ready Trust

Bu milestone ile proje bir adim daha ileri gitti.

Burada:

- final karar seti netlesti: `APPROVED | CONDITIONAL | REJECTED`
- internal exception state `NEEDS_REVIEW` internal-only hale geldi
- raw ve flat artefact contract'lari null-free ve parity-safe hale getirildi
- collection run altina calibration, operator packet ve operator briefing geldi
- planner source mix daha durust raporlanmaya baslandi
- pilot refresh, artifact QA ve explanation pack katmani eklendi

Bu milestone'un en kritik farki su:

Sistem artik sadece "iyi gorunen planlar" ureten bir yapi degil.
Ayni zamanda karar sahipligi, artefact guveni ve pilotta tekrar edilebilir isletim disiplini olan bir yapi.

### v2.1 sonrasi output integrity duzeltmeleri

Bu rehber acisindan son onemli gelisme, v2.1 sonrasinda yaptigimiz output integrity fix dalgasidir.

Bu dalgada:

- `critical_field_null_count` stale kalmayacak sekilde yeniden canonical hale getirildi
- `raw_contract_pass` normalize edilmis summary uzerinden hesaplaniyor
- `customer_plans.csv` validated subset degil, full candidate provenance tasiyor
- `dice` best plan'lar artik flat artefact'lerde gorunur
- sahte `DATA_ISSUE` conditionals temizlendi
- `REJECTED` musteri artik `week_4` gibi approval-implying readiness ile dis yuzeye cikmiyor

Yani bugunku output'lari okurken sunu varsayabilirsin:

- contract health metriği artik daha guvenilir
- data issue sayisi artik gercek issue'lara daha yakin
- plan source audit'i artik flat artefact uzerinden yapilabilir

---

## 10. Bugun bu projede en onemli gucler neler?

Benim gordugum en guclu taraflar bunlar:

### 10.1 Tek bir model degil, katmanli sistem

Bu iyi bir sey.
Cunku kredi karari gibi zor alanlarda tek basina model yetmez.

### 10.2 Engine source of truth

Website veya demo kendi anlamini uydurmuyor.
Asil dogru Python motorundan geliyor.

### 10.3 Deterministic decision owner var

Bu artik cok kritik bir guc.

Sistem:

- bir customer-level decision payload uretir
- bunu raw, flat, operator packet ve proof surface boyunca ayni mantikla tasir
- farkli yuzeyler kendi kararini icat etmez

Bu, fintech benzeri urunlerde guven icin cok degerlidir.

### 10.4 "More honest than impressive" yaklasimi

Bu proje sadece parlatilmis uplift gostermiyor.
Sunlari da gostermeye calisiyor:

- gerceklesme zorlugu
- execution gap
- false optimism
- weak 4w health

Bu urun guveni icin cok onemli.

### 10.5 Pilot-ready dusunulmus

Canli entegrasyon yoksa bile,
kuruma gidecek paket mantigi kurulmus.
Bu, projeyi akademik demo olmaktan cikarip urun yoluna sokuyor.

### 10.6 Portfolio inspection lane var

Sistem artik tek musteri artifact'iyle sinirli degil.
50-100 musteri gibi toplu koleksiyonlarla:

- action dagilimi
- constraint dagilimi
- execution-aware sonuc
- portfoyde en sik gorulen plan yapisi

incelenebiliyor.

### 10.7 Operator review lane var

Artik ciktilar sadece ML gozlemi icin degil.
Operator veya analist akisi icin de paketleniyor.

Burada:

- per-customer operator packet
- collection-level operator briefing
- calibration ve queue guidance

gibi katmanlar var.

Bu, "demo" ile "gercek kullanim provasi" arasindaki farki daraltiyor.

---

## 11. Hala hangi alanlar acik?

Proje guclu bir seviyede ama tamamlanmis degil.

Acik tasinan ana alanlar:

- dis kurum entegrasyonlari
- daha derin institution deployment akislari
- readiness semantiklerinin daha da rafine edilmesi
- approval oranini yukseltecek planner / policy tuning
- kurum tarafli policy / kurum teklifi sync'in daha ileri versiyonlari

Yani sistem artik iyi bir "beyin" ve iyi bir "urun demosu" seviyesinde.
Siradaki buyuk adim daha derin entegrasyon ve operasyonel otomasyon olur.

## 11.1 Bugun ne production-ready, ne degil?

Bu bolum bilerek durust yazildi.
Cunku bu projeyi dogru anlatmanin en iyi yolu, hem guclu hem acik alanlari birlikte gostermek.

### Bugun guclu olanlar

- semantic action planning
- numeric targets
- deterministic decision ownership
- contract / parity trust
- feasibility ve execution truth
- kurum teklifi katmani
- product surface
- portfolio inspection lane
- operator packet ve pilot baseline

### Henuz tam production-ready olmayan alanlar

- canli kurum entegrasyonlari
- surekli refresh ve monitoring otomasyonunun daha ileri hali
- institution-specific deployment flow'lari
- approval funnel tuning
- readiness semantics'in daha ince is kurali seviyesine tasinmasi

Bu ne demek?

Sistemin cekirdek akli ve inceleme yapisi guclu.
Ama "kuruma tam canli baglanalim ve sonsuz otomasyonla akalim" seviyesinde degil.

---

## 12. Ciktilari incelerken nereye bakmali?

### 12.1 Single-customer artifacts

Eger tek musteriye bakiyorsan:

- `credit-coach/artifacts/runs/<run_id>/tables/customer_roadmap.json`
- `credit-coach/artifacts/runs/<run_id>/tables/plans.json`
- `credit-coach/artifacts/runs/<run_id>/metrics.json`
- `credit-coach/artifacts/runs/<run_id>/tables/customer_roadmap_steps.csv`
- `credit-coach/artifacts/runs/<run_id>/tables/operator_packet.json`
- `credit-coach/artifacts/runs/<run_id>/tables/operator_packet.md`

Burada en kritik alan artik `customer_roadmap.json` icindeki `summary` bolumudur.

Ozellikle bak:

- `decision_status`
- `decision_status_internal`
- `decision_confidence`
- `expected_readiness`
- `decision_reason_summary`
- `decision_reason_primary`
- `upgrade_condition`
- `best_plan_source`
- `raw_contract_pass`
- `parity_pass`

### 12.2 Batch / collection artifacts

Eger toplu inceleme yapiyorsan:

- `credit-coach/artifacts/runs/<run_id>/tables/customer_artifact_collection/flat/customer_metrics.csv`
- `credit-coach/artifacts/runs/<run_id>/tables/customer_artifact_collection/flat/customer_plans.csv`
- `credit-coach/artifacts/runs/<run_id>/tables/customer_artifact_collection/flat/customer_roadmap_steps.csv`
- `credit-coach/artifacts/runs/<run_id>/tables/customer_artifact_collection/collection_summary.md`
- `credit-coach/artifacts/runs/<run_id>/tables/customer_artifact_collection/calibration/funnel_summary.json`
- `credit-coach/artifacts/runs/<run_id>/tables/customer_artifact_collection/calibration/status_by_readiness.csv`
- `credit-coach/artifacts/runs/<run_id>/tables/customer_artifact_collection/calibration/policy_comparison.csv`
- `credit-coach/artifacts/runs/<run_id>/tables/customer_artifact_collection/operator_review_briefing.md`
- `credit-coach/artifacts/runs/<run_id>/tables/customer_artifact_collection/operator_packets/`

Burada yeni okuma mantigi su:

- `collection_summary.md` = hizli genel tablo
- `customer_metrics.csv` = customer-level truth
- `customer_plans.csv` = plan source provenance ve candidate audit
- `status_by_readiness.csv` = readiness ile karar uyumu
- `operator_review_briefing.md` = operasyonel onceliklendirme

### 12.3 Website demo artifacts

Eger urun / proof tarafina bakiyorsan:

- `credit-coach-website/demo-data/single_customer_roadmap.json`
- `credit-coach-website/demo-data/product_confidence_snapshot.json`

Ama cok kritik not:

Website snapshot'lari her zaman en guncel engine run'i olmayabilir.
Gercek kaynak olarak engine artifact'lerini esas almak daha dogru olur.

### 12.4 Pilot / production baseline artifacts

Pilot proof tarafina bakiyorsan su artefact'ler artik first-class:

- `pilot_refresh_manifest.json`
- `pilot_refresh_summary.md`
- `artifact_qa_summary.json`
- `release_smoke_summary.json`
- `decision_explanation_pack.json`

Bu dosyalar su sorulara cevap verir:

- bu pilot refresh hangi version ile uretildi?
- package QA temiz mi?
- smoke sonucu ne?
- kuruma gosterecegimiz explanation artefact'i ne durumda?

### 12.5 Ilk inceleme checklist'i

#### Tek musteri incelerken

- `decision_status` ne?
- `decision_reason_summary` mantikli mi?
- `expected_readiness` ile karar uyumlu mu?
- `upgrade_condition` is diliyle anlamli mi?
- `raw_contract_pass = 1` mi?
- `parity_pass = 1` mi?
- `best_plan_source` ne?
- numeric target mantikli mi?
- kurum teklifi var mi?

#### Portfoy incelerken

- `approved_share / conditional_share / rejected_share` nasil?
- `approve_plus_conditional_share` ne durumda?
- `critical_field_null_rate` ve `raw_contract_pass_rate` temiz mi?
- `parity_mismatch_count` var mi?
- `conditional hotspots` gercekten is nedeni mi, yoksa data issue mi?
- `best_plan_source` dagilimi nasil?
- `customer_plans.csv` ile `customer_metrics.csv` best source tarafinda uyumlu mu?
- readiness dagilimi kararlarla tutarli mi?

### 12.6 Son integrity fix'lerden sonra output'lari nasil okumali?

Bu kisim ozellikle onemli.
Cunku son yaptigimiz duzeltmeler output'larin anlamini degistirdi.

Artik:

- `critical_field_null_rate = 0` ise bunu daha guvenle okuyabilirsin
- `raw_contract_pass_rate` gercekten contract health'i temsil eder
- `DATA_ISSUE` sayisi, eskiye gore daha cok gercek contract/parity sorunu demektir
- `customer_plans.csv` icindeki `plan_source` artik audit icin kullanilabilir

Ama sunu da akilda tut:

- approval funnel halen zayif olabilir
- bu, her zaman contract bug'i anlamina gelmez
- bazen gercekten planner quality veya policy threshold konusu olabilir

Yani yeni dogru siralama su:

1. once contract health'e bak
2. sonra source provenance'a bak
3. sonra readiness ve operator packet'e bak
4. en son approval / conditional tuning'i yorumla

---

## 13. Bu projeyi ogrenmek icin en iyi okuma sirasi

Eger sifirdan ogrenmek istiyorsan sana su sirayi oneririm:

1. Bu dokumani oku.
2. `credit-coach/README.md` dosyasini oku.
3. `.planning/PROJECT.md` dosyasini oku.
4. `.planning/MILESTONES.md` dosyasini oku.
5. `credit-coach/src/credit_coach/cli/run_train.py` dosyasini oku.
6. `credit-coach/src/credit_coach/cli/run_recourse.py` dosyasini oku.
7. `credit-coach/src/credit_coach/decision/ownership.py` dosyasini oku.
8. `credit-coach/src/credit_coach/recourse/` klasorunu gez.
9. `credit-coach/src/credit_coach/coaching/messaging.py` dosyasina bak.
10. `credit-coach/src/credit_coach/evaluation/portfolio_validation.py` dosyasina bak.
11. `credit-coach/src/credit_coach/cli/run_pilot_baseline_refresh.py` dosyasina bak.
12. En son `credit-coach-website/TECH_ARCHITECTURE.md` ile website tarafini oku.

Bu sirayla gidersen once "ne"yi, sonra "nasil"i, sonra "neden"i anlarsin.

### 13.1 Kim ne okumali?

- **urun yoneticisi** -> 1, 2, 3, 10, 11, 12
- **ML / data science** -> 3, 4, 5, 7, 8, 10
- **frontend / website** -> 4, 8.2, 10, 12
- **yeni katilan herkes** -> 1, 2, 6, 7, 13, 14

---

## 14. Tek cumlede kapanis

Credit Coach, kredi riski tahmin eden bir modelin ustune kurulu; ama asıl degeri, bu tahmini gercek dunyada uygulanabilir aksiyonlara, kurum tekliflerine, urun anlatilarina ve portfoy kanitina ceviren katmanli karar sistemi olmasinda.
