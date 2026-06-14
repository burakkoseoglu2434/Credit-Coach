# Credit Coach

## Yatirimci Sunumu

**Versiyon:** `v1.2` sonrasi  
**Tarih:** 2026-03-16

## 1. Kisa Ozet

Credit Coach, kredi veren kurumlar icin gelistirilmis bir karar-istihbarati platformudur.

Bugun cogu kredi sistemi sadece iki sey soyler:

- onay
- red

Credit Coach ise daha degerli bir soruya odaklanir:

**"Bugun reddedilen hangi musteriler, guvenli ve kontrollu bir sekilde onay bandina tasinabilir ve bunun en iyi yolu nedir?"**

Bu proje, klasik kredi skorlama motorunun ustune oturan daha akilli bir katmandir. Sadece risk tahmini yapmaz; ayni zamanda:

- reddedilen musteri icin gercekci iyilestirme planlari uretir
- gerektiginde kurum tarafli teklifleri de denkleme katar
- fairness, reliability ve operasyonel kontrol katmanlarini korur
- zaman icinde sonuc verilerinden ogrenebilen bir altyapi kurar

Bugun elimizde sadece bir fikir ya da demo yok. Projenin cekirdegi uc farkli shipped milestone sonunda anlamli olgunluga ulasmis durumda. `v1.2` ile birlikte sistem:

- daha gercekci aksiyonlar uretebiliyor
- kullanicinin o aksiyonlari uygulama ihtimalini hesaba katiyor
- tek adimli degil, fazli yol haritalari kurabiliyor
- kurum tarafli teklif optimizasyonu yapabiliyor
- sonuc verisini ogrenme dongusune baglayabiliyor

Ayni zamanda durust olmak gerekirse, bu henuz:

- tam paketlenmis enterprise urun degil
- son kullaniciya acik bir borclu uygulamasi degil
- canli kurumsal entegrasyonlari tamamlanmis bir banka platformu degil

Bu da projeyi yatirim acisindan ilgi cekici hale getiriyor: teknik cekirdek ciddi sekilde kurulmus, fakat ticarilesme ve urunlesme alani hala acik.

## 2. Problem Ne?

Geleneksel kredi karar sistemleri, reddedilen musteriyi cogu zaman kayip musteri olarak gorur.

Bu yaklasim hem musteri hem kurum icin verimsizdir.

### Musteri tarafinda

- neden reddedildigini tam anlayamaz
- ne yaparsa onaya yaklasacagini bilmez
- sistem ona bir sonraki adimi soylemez

### Kurum tarafinda

- geri kazanilabilir musteri kaybedilir
- buyume ekibi daha fazla onay isterken risk ekibi daha sert kontrol ister
- fairness, aciklanabilirlik ve audit ihtiyaci arttikca operasyon daha zorlasir

Kisaca sorun su:

**kredi dunyasi sadece daha iyi skor degil, daha iyi karar-sonrasi yonetim katmani istiyor.**

## 3. Credit Coach Ne Yapiyor?

Credit Coach, kredi kararini bir "sonuc" olmaktan cikarip bir "surec"e donusturur.

Yuksek seviyede dort sey yapar:

1. Musterinin riskini tahmin eder ve ana nedenleri aciklar.
2. Reddedilen musteri icin uygulanabilir aksiyon planlari uretir.
3. Bu planlarin guvenli, adil, uygulanabilir ve operasyonel olarak kabul edilebilir olup olmadigini kontrol eder.
4. Gercek sonuclardan ogrenerek zamanla daha iyi kararlar vermeye hazir hale gelir.

Boylece kurum su noktadan:

**"Bu musteri reddedildi."**

su noktaya gecmeye baslar:

**"Bu musteri bugun reddedildi ama iki farkli guvenli iyilestirme yolu var; biri daha hizli, biri daha guvenli, biri de kurum tarafli teklif ile desteklenebilir."**

Bu, klasik skor modelinden farkli bir urun kategorisidir.

## 4. Neden Ticari Olarak Degerli?

Credit Coach ayni anda uc farkli ihtiyaca dokunur:

- risk ve model governance
- conversion ve portfoy buyumesi
- tahsilat, yapilandirma ve musteri geri kazanimi

Bu cok onemli, cunku finans kurumlari genelde bu alanlari ayrik sistemlerle yonetir.

Dogru urunlesme ile Credit Coach zamanla su alanlara yayilabilir:

- red alan musteriyi sonradan onaya tasima
- near-prime segment yonetimi
- kurum teklifleri ve yapilandirma yollarinin secimi
- tahsilat ve recovery optimizasyonu
- policy denemeleri ve portfoy etkisi analizi

Yani bu sadece "skorlamayi biraz iyilestirelim" urunu degil; dogru kuruldugunda **lending optimization layer** olma potansiyeli tasiyor.

## 5. Musteri Kim?

En mantikli ilk musteri segmenti **B2B** tarafta:

- bankalar
- dijital kredi sirketleri
- tuketici finansmani oyunculari
- BNPL veya embedded finance sirketleri
- kredi karar, underwriting veya servicing altyapisi sunan platformlar

En dogru ilk urun formu da su gorunuyor:

- API + operator dashboard

Bu, projenin tarihsel yonuyle de uyumlu:

- once kurum tarafina sat
- sonra isterse borrower-facing katman ac

## 6. Bugune Kadar Gercekten Ne Insaa Edildi?

Bu kisim yatirimci icin en kritik yer. Proje sadece "AI ile kredi" fikri degil; somut bir build zinciri var.

### v1.0 ile kurulan temel

Ilk buyuk blokta su altyapi kurulmus durumda:

- deterministik model egitimi
- kredi risk skorlama
- aciklanabilirlik
- recourse plan uretimi
- benchmark ve challenger akislari
- telemetry ve audit altyapisi
- production smoke benzeri operasyonel kontroller

Bu onemli, cunku bugunku recommendation katmani zayif bir zemin uzerine oturmuyor.

### v1.1 ile governance sertlestirildi

Ikinci milestone ile:

- fairness release semantics
- KPI contract tutarliligi
- candidate-quality kaniti
- telemetry-gated release pack mantigi
- business-proxy outcome ozetleri

standartlasti.

Bu da su anlama geliyor:

kurumlara satilabilir bir sistem icin gerekli olan "kontrol ve izlenebilirlik" omurgasi kuruldu.

### v1.2 ile recommendation motoru ciddi sekilde olgunlasti

En son tamamlanan milestone olan `v1.2`, projeyi baska bir seviyeye tasidi.

Eklenen baslica yetenekler:

- ham feature edit yerine typed aksiyonlar
- execution probability tabanli davranis farkindalikli siralama
- tek adim yerine fazli trajectory yapisi
- kurum tarafli offer optimization
- learning loop ve off-policy evaluation altyapisi

Bu kombinasyon, projeyi basit bir "akilli kural motoru" olmaktan cikarip daha genis bir **adaptive recommendation engine** haline getiriyor.

## 7. Urun Bugun Ne Yapabiliyor?

Bugunku repo durumuna gore sistem:

- reddedilen musteri icin yapilandirilmis iyilestirme plani uretebiliyor
- musteri aksiyonu ile kurum teklifini ayri ama birlikte ele alabiliyor
- teorik etkiyi degil, gercekciligi de ranking’e katabiliyor
- zaman icinde fazli ilerleme plani kurabiliyor
- fairness, reliability ve telemetry kurallarini koruyabiliyor
- karar ve outcome log’larini daha sonra ogrenmeye uygun sekilde tutabiliyor
- farkli policy yaklasimlarini offline olarak karsilastirabiliyor

Bu su demek:

Sirket sifirdan "bir model" kurmuyor. Elinde urune donusebilecek derin bir engine var.

## 8. Henuz Eksik Olanlar Neler?

Bu henuz tamamen paketlenmis ticari urun degil. En buyuk eksikler:

- operator tarafli dashboard ve kurumsal workflow katmani
- daha zengin compliance ve adverse-action anlatimi
- dis sistem entegrasyonlari
- canli pilot ve ticari uygulama kaniti
- daha net urun paketleme ve GTM katmani

Bu aslinda yatirim tezi icin olumlu bir denge yaratiyor:

- cekirdek teknoloji olgun
- urunlesme ve ticarilesme alani hala acik

## 9. Bu Neden Guclu Bir Girisim Hikayesi Olabilir?

### 1. Pahali bir is akisini hedefliyor

Reddedilen kredi basvurulari, finans tarafinda buyuk bir kayip havuzu yaratir. Bu musterilerin bir kismi guvenli sekilde geri kazanilabilirse dogrudan ticari deger uretilir.

### 2. Bu sadece bir model degil, sistem

Bir cok ekip daha iyi skor uretebilir. Daha az ekip su kombinasyonu bir araya getirebilir:

- risk
- fairness
- explainability
- recourse
- institution-side offers
- outcome learning

Bu sistem derinligi, savunulabilirlik yaratir.

### 3. Dar bir kama ile buyuk platforma acilabilir

Ilk urun cokturu net olabilir:

- red alan musteriden deger geri kazanmak

Ama zamanla ayni altyapi su alanlara genisleyebilir:

- collections
- restructuring
- policy experimentation
- portfolio intelligence

### 4. Veri moati olusturma potansiyeli var

Kararlar, secilen planlar, uygulama davranisi, teklif kabul davranisi ve gercek outcome verileri biriktikce sistemin tavsiye kalitesi artar. Bu zamanla guclenen bir moat uretebilir.

## 10. Is Modeli Nasil Kurulabilir?

En mantikli ilk model kurumsal yazilim gibi gorunuyor.

### Ilk gelir modeli

- yillik lisans
- onboarding / implementation ucreti
- kullanim veya batch bazli fiyatlama

### Urun paketi

- decision support API
- operator dashboard
- governance ve analytics raporlama
- premium moduller: offer optimization, learning insights, policy comparison

### Uzun vadeli genisleme

- portfoy zekasi
- policy simulation
- recovery intelligence
- lender workflow icine gomulu recommendation katmani

Bu model, B2C uygulamaya gore daha hizli ve daha yuksek birim gelir potansiyeli tasir.

## 11. Elimizdeki Kanit Ne?

Buradaki en guclu kanit tipi su an icin **ticari traction degil, urun ve muhendislik olgunlugu**.

Bu ayrimi net tutmak lazim.

Bugun repo’da gercek olan seyler:

- `v1.0`, `v1.1` ve `v1.2` milestone’lari tamamlandi
- `v1.2` milestone audit’ten gecti
- sistem typed actions, behavior-aware ranking, trajectory, offer optimization ve learning loop seviyesine geldi
- fairness, governance, telemetry, challenger ve offline learning icin ciddi bir artifact ve test disiplini var

Ayrica proje materyallerinde yer alan dahili sinyaller sunlari isaret ediyor:

- redden onaya donus tarafinda anlamli ic benchmark iyilesmeleri
- fairness gap’lerinde dusus
- latency ve candidate diversity tarafinda olculebilir ilerleme

Bunlar **uretken sistemin dahili kanitlari** olarak degerlidir; henuz dis dunyada yayinlanmis musteri case study’si gibi okunmamalidir.

## 12. Neden Simdi?

Pazar zamani da mantikli:

- kurumlar buyume isterken risk kontrolunu kaybetmek istemiyor
- explainability ve fairness beklentisi yukseliyor
- kurumlar tam otonom AI’dan cok kontrollu karar-istihbarati katmanlarina daha yakin duruyor
- offline policy evaluation gibi yapilar regule ortamlarda daha degerli hale geliyor

Credit Coach burada dogru pozisyonda:

**tam otomasyon once degil, once guvenilir karar zekasi**

Bu, satin alma psikolojisi acisindan daha gercekci.

## 13. Yatirim Gelirse En Dogru Kullanimi Ne Olur?

Yeni sermaye en cok su alanlarda deger yaratir:

- engine’i enterprise urune cevirmek
- operator dashboard ve kurumsal workflow katmani kurmak
- banka/fintech entegrasyonlarini yapmak
- pilot musteriler almak
- compliance ve anlatim katmanini guclendirmek
- ticari ROI raporlamasini netlestirmek

Yani bundan sonraki para, cekirdegi "icad etmek" icin degil, cekirdegi **satilabilir sistem**e cevirmek icin kullanilmali.

## 14. Baslica Riskler

### Ticari risk

Teknik cekirdek urun paketlemeden daha ileride. Bu iyi bir sey ama ticari kapanis icin urunlesme hizinin yetismesi gerekir.

### Entegrasyon riski

Finans kurumlari yalnizca iyi motor satin almaz. Mevcut sistemlerine ve kontrol yapilarina uyum ister.

### Guven ve compliance riski

Governance omurgasi guclu olsa bile canli kullanim icin anlatim, approval flow ve operasyonel katmanlarin da tamamlanmasi gerekir.

### Fokus riski

Proje underwriting, recourse, offers, collections, dashboard ve borrower UX gibi birden cok yone acilabilir. Ilk wedge’in dagitilmamasi gerekir.

## 15. Ana Yatirim Tezi

Eger lending dunyasinin statik approve/deny akisindan, daha akilli, aciklanabilir ve outcome-aware karar sistemlerine gececegine inaniyorsak, Credit Coach bir fikir asamasi projesi degil.

Asil tez su:

**onemli bir recommendation-and-governance engine zaten kurulmus durumda; bundan sonraki yatirim bu engine’i kurumsal urune donusturebilir.**

---

## Yatirimcinin Sorabilecegi Sorular ve Cevaplari

## 1. Bu sirket tam olarak ne satiyor?

En dogru cevap: kredi veren kurumlara yonelik bir karar-istihbarati urunu satiyor. Ilk paket buyuk ihtimalle API + dashboard + governance raporlama kombinasyonu olur.

## 2. Bu, sadece daha iyi bir kredi skoru mu?

Hayir. Daha iyi skor sadece kimin riskli oldugunu soyler. Credit Coach ise hangi musterinin nasil iyilesebilecegini, hangi yolun daha gercekci oldugunu ve hangi kurum teklifinin daha anlamli oldugunu soyler.

## 3. Ilk musteri B2C mi B2B mi?

En guclu ilk wedge B2B. Banka, fintech veya lender altyapisina satmak daha hizli gelir ve daha net ROI yaratir.

## 4. Bugun gercekten ne var?

Gercek olan sey engine’in kendisi. Typed actions, behavior-aware ranking, phase-based trajectories, offer optimization ve learning loop altyapisi repo icinde mevcut. Eksik olan kisim daha cok packaging, dashboard, entegrasyon ve pilotlar.

## 5. Musteri veya gelir var mi?

Bu repo’dan musteri veya gelir oldugunu soylemek dogru olmaz. Buradaki guclu kanit ticari traction degil; teknik ve urunsel olgunluk.

## 6. Para nasil kazanilir?

Muhtemelen yillik lisans + kurulum + kullanim bazli enterprise model ile. Ileride premium modullerle hesap basina gelir artabilir.

## 7. En buyuk moat ne?

Moat tek bir model degil. Risk, recourse, fairness, telemetry, offer logic ve outcome learning’in ayni sistemde birlesmesi. Bu butunluk, kopyalamasi daha zor bir urun zemini olusturur.

## 8. Regulator veya governance acisindan neden guvenilir olabilir?

Cunku proje en basindan governance’i urunun bir parcasi olarak ele aliyor. Fairness, reliability, telemetry ve audit mantigi sonradan eklenmis yamalar degil.

## 9. Teknik olarak en zor kisim ne?

Plan uretmek degil; gercekci, uygulanabilir, guvenli, adil ve ticari deger ureten plani ayni anda uretmek. Zorluk ve savunulabilirlik burada.

## 10. Bu ileride baska alanlara genisler mi?

Evet. Red recovery ile baslayip offers, restructuring, collections, recovery optimization ve policy experimentation alanlarina genisleyebilir.

## 11. Bu neden bir feature degil de sirket olabilir?

Eger urun, lender’in risk-buyume-governance dengesini yonettigi temel control layer haline gelirse, bu sadece bir ozellik olmaktan cikar. Ana is akisina oturur.

## 12. Ciddi bir fundraise oncesi ne eksik?

Uc sey en cok deger katar:

- net operator urunu
- 1-2 pilot musteri
- kurumsal ROI’yi gosteren case-style raporlama

## 13. Bundan sonraki 12-18 ayda basari nasil gorunur?

Basarili bir yol haritasi soyle gorunur:

- yeni milestone’un net tanimlanmasi
- dashboard + API urunlesmesi
- canli veya near-live pilotlar
- conversion, governance ve recovery etkisini gosteren ROI kaniti
- tekrar edilebilir bir commercial packaging

## 14. Yatirim parasi teknik tarafa mi urun tarafina mi gitmeli?

Bu asamadan sonra daha cok urunlesme, entegrasyon, pilot ve compliance anlatim katmanina gitmeli. Cekirdek motor zaten anlamli olgunluga ulasmis durumda.

## 15. Bu proje neden ilginc?

Cunku AI ile kredi alaninda pek cok proje sadece tahmin yapiyor. Credit Coach ise tahmini, aksiyona, aksiyonu kurumsal karara, karari da ogrenme dongusune baglamaya calisiyor. Bu onu daha buyuk bir urun sinifina tasiyor.
