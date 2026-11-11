# ADR-007: Güvenlik payı δ

Durum: **Kural kabul edildi; ölçüm yapıldı (aşağıda).** Kural bölümü ölçümden ÖNCE yazıldı ve commit'lendi (`af1ac10`).

> Kredi veren: tek fiyatlı kurgusal kredi veren.

## Bağlam
Bir plan, modelin plan sonrası riskinin (`p_high`) onay eşiğinin `δ` kadar altına inmesini gerektirir
(ADR-006: `p_after < eşik − δ`). Bugüne kadar `δ = 0,02` kullanıldı ve "varsayım" etiketliydi
(`configs/catalog/demo_v0.yaml`, `delta.deger`). `δ`, Venn-Abers aralığı değildir: aralık zaten
`p_high` içindedir; `δ` dönem kayması ve model belirsizliği için üstüne konan ayrı bir paydır.

## Kural
`δ`, ölçümle şu kuralla türetilir:

1. **Aylar:** kalibrasyon dilimi (2015-03..06) ve boşluk ayları (2015-01, 02, 07, 08): sekiz ay.
   Test dilimi (2015-09..12) kullanılmaz.
2. **Kayıtlar:** her ayda, 36 aylık olgunlaşmış kohortun TÜM kayıtları (destek içi ya da dışı
   ayrımı yapılmaz; karar ya da ret ayrımı yapılmaz).
3. **Kalibre ortalama PD (`m_ay`):** ayın kayıtlarında dondurulmuş model ve kalibratörün nokta
   tahmini `p_point`'in ortalaması.
4. **Gözlenen oran (`g_ay`):** ayın kayıtlarında gözlenen temerrüt oranı (etiketler yalnızca bu
   değerlendirme içindir, karar yoluna girmez).
5. **Aylık kayma:** `kayma_ay = |m_ay − g_ay|`.
6. **Kural:** `δ = en büyük kayma_ay`, **0,001'e yukarı yuvarlanır**
   (`δ = ceil(1000 × en büyük kayma_ay) / 1000`).

## Notlar (ölçümden önce)
- Kalibrasyon ayları kalibratörün eğitim verisidir (örneklem içi); boşluk ayları örneklem dışıdır.
  Her iki gruptaki aylar birlikte alınır, bir grup diğerine tercih edilmez.
- `δ` bir **varsayımdır**: ölçülmüş bir kapsama özelliği taşımaz ve gelecek dönemler için
  geçerliliği bilinmez. Kural ölçümden sonra değiştirilmez; yalnızca hesaplanan değer katalogdaki
  değerden farklıysa değer güncellenir.
- Katalogdaki değer (`delta.deger`) bu kuralın sonucudur ve API, arayüz ve raporlar onu kullanır.

## Ölçüm sonucu
<!-- OLCUM-BASLANGIC -->
Ölçüm (`python -m credit_coach.safety_margin`; ham veri gerekir; test dilimi yok). Fark = kalibre ortalama PD − gözlenen oran:

| ay | dilim | kayıt | kalibre ortalama PD | gözlenen oran | fark | aylık kayma |
|---|---|---|---|---|---|---|
| 2015-01 | boşluk | 23631 | 0.1545 | 0.1488 | +0.0057 | 0.0057 |
| 2015-02 | boşluk | 16023 | 0.1535 | 0.1417 | +0.0118 | 0.0118 |
| 2015-03 | kalibrasyon | 16914 | 0.1555 | 0.1540 | +0.0015 | 0.0015 |
| 2015-04 | kalibrasyon | 23619 | 0.1549 | 0.1554 | -0.0005 | 0.0005 |
| 2015-05 | kalibrasyon | 21539 | 0.1544 | 0.1523 | +0.0021 | 0.0021 |
| 2015-06 | kalibrasyon | 19064 | 0.1528 | 0.1536 | -0.0008 | 0.0008 |
| 2015-07 | boşluk | 30864 | 0.1508 | 0.1462 | +0.0046 | 0.0046 |
| 2015-08 | boşluk | 23938 | 0.1474 | 0.1425 | +0.0050 | 0.0050 |

En büyük aylık kayma: **0.011832** (2015-02, boşluk). Kural: δ = ceil(1000 × 0.011832) / 1000 = **0.012**.
<!-- OLCUM-BITIS -->

## Karar ve etki
Kuralın hesapladığı değer **δ = 0,012** (en büyük aylık kayma 0,011832, 2015-02, boşluk ayı), katalogdaki
**0,02'den farklıdır**; bu yüzden `configs/catalog/demo_v0.yaml` içindeki `delta.deger` güncellendi
(gerekçe aynı dosyadaki etiketle birlikte yazılı; etiket "varsayım" olarak kalır).
Katalog değeri: 0,012.

Önceki varsayılanla (δ = 0,02) yeni varsayılanın (δ = 0,012) karşılaştırması, reddedilenler içinde
(kalibrasyon 52.229, boşluk 59.529; test dilimi yok; raporlar yeniden üretildi):

| ölçü | dilim | δ = 0,02 | δ = 0,012 |
|---|---|---|---|
| en az bir yolda plan | kalibrasyon | 19,1% | 19,1% |
| en az bir yolda plan | boşluk | 19,4% | 19,4% |
| PLAN_YOK | kalibrasyon | 80,9% | 80,9% |
| GUCLU | kalibrasyon | 0,1% | 1,1% |
| KOSULLU | kalibrasyon | 1,5% | 10,0% |
| ZAYIF | kalibrasyon | 17,5% | 8,0% |
| GUCLU | boşluk | 0,1% | 1,2% |
| KOSULLU | boşluk | 1,7% | 10,4% |
| ZAYIF | boşluk | 17,6% | 7,9% |

Plan oranı değişmedi (aşağıdaki plato nedeniyle); etiket dağılımı belirgin değişti, çünkü
`min_phi = (p_önce − kesim) / Δ` ve kesim = eşik − δ doğrudan δ'ya bağlıdır.

## Plato notu
Venn-Abers kalibratörü basamaklıdır (ölçüm: `docs/demo_recourse_delta_diag.md`): aday planların
`p_after` değerleri eşik civarında birkaç platoda toplanır (örneğin 0,0861; 0,0997; 0,1009).
Eşik − 0,02 ile eşik − 0,01 arasında yalnızca **14 aday** vardır (eşik − 0,03 ile eşik − 0,02
arasında 24.527, eşik − 0,01 ile eşik − band arasında 35.003). Sonuç: δ'nın 0,01-0,02 arasındaki
değerleri plan oranını neredeyse değiştirmez; δ = 0,01 ve δ = 0,02 aynı plan oranı tablosunu verdi
(yol başına kayıt sayıları en çok bir kayıtla farklı). Bu yüzden δ seçimi küçük aralıklarda duyarlı
değildir, 0,03'e doğru ya da band'a doğru gidildiğinde duyarlıdır.
Plan oranı platoya takıldığı için δ = 0,02 → 0,012 değişikliğinde değişmedi; ama **etiket dağılımı
δ'ya plan oranından çok daha duyarlıdır** (yukarıdaki tablo): aynı planlar daha düşük gereken etki
payı gösterir. Etiket eşikleri (0,50 / 0,75) da varsayımdır; δ ve eşikler birlikte yorumlanmalıdır.
