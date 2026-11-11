# Demo v0: örnek vakaların seçim kuralı

> Kredi veren: tek fiyatlı kurgusal kredi veren.

Bu kural, kayıtlar aranmadan ÖNCE yazıldı ve commit'lendi. Kayıtlar bulunduktan sonra kural
değiştirilmez; kayıt bulunamazsa kural gevşetilmez, durum raporlanır.

## Mevcut beş vaka
`onay`, `koşullu`, `ret + plan`, `ret + PLAN_YOK`, `değerlendirilemez`: seçimleri hafta 8-9'da
yapıldı (`credit_coach.ui_cases`). Bu belgeyle DEĞİŞMEZ: `frontend/src/ornekler.json` içindeki ilk
beş kayıt ve `frontend/public/ornek_toplu.csv` aynen kalır.

## Eklenen iki vaka: kural
**Dosya sırasındaki ilk GUCLU / ilk KOSULLU reddedilen kayıt, δ varsayılan.**

- **Dosya ve sıra:** `tests/golden/inputs_v1.jsonl`, yalnızca gerçek kalibrasyon kayıtları
  (`cal-` ile başlayan kimlikler), dosyadaki sırayla. Sentetik kayıtlar ve değiştirilmiş
  varyantlar kullanılmaz.
- **Reddedilen:** kaydın `/score` yanıtında `dis_durum` değeri `REJECTED` ve `destek_ihlalleri` boş.
- **δ:** API'nin varsayılanı (`configs/catalog/demo_v0.yaml`, `delta.deger`); δ ayrıca verilmez.
- **Etiket:** yanıttaki planın (`PLAN`) yollarındaki en güçlü `dayaniklilik` etiketi
  (sıra: GUCLU, KOSULLU, ZAYIF). Planı olmayan (`PLAN_YOK`) kayıt GUCLU ya da KOSULLU sayılmaz.
- **`ret_guclu`:** en güçlü etiketi GUCLU olan ilk kayıt.
- **`ret_kosullu`:** en güçlü etiketi KOSULLU olan ilk kayıt.
- **Doğrulama:** kategori, kaydın kendi `/score` yanıtından okunur (API'da doğrulanır); `p_point`
  değeri golden dosyasındakiyle 1e-9 içinde aynı olmalıdır.
- **Tarih:** `basvuru_tarihi` mevcut vakalarla aynı yolla, ham veriden kaydın ihraç ayı (ay başı).
- **Sıra:** yeni vakalar mevcut beş vakadan sonra gelir; anahtarlar `ret_guclu` ve `ret_kosullu`.

## Sonuç
Kayıtlar henüz aranmadı.
