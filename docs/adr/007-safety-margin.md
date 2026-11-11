# ADR-007: Güvenlik payı δ

Durum: **Kural kabul edildi; ölçüm henüz yapılmadı.** Bu bölüm ölçümden ÖNCE yazıldı ve commit'lendi.

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

## Sonuç
Ölçüm henüz yapılmadı.
