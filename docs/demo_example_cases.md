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

## Sonuç (kural uygulandı, kural değiştirilmedi)
198 gerçek kayıt dosya sırasıyla `/score`'dan geçirildi (δ varsayılan). Reddedilen, planı olan
kayıtların en güçlü yol etiketi dağılımı: GUCLU 0, KOSULLU 6, ZAYIF 31. Reddedilen olmayan ya da
planı olmayan kayıtlar: 161.

| anahtar | kayıt | durum |
|---|---|---|
| `ret_guclu` | yok | **Bulunamadı:** 198 gerçek kayıtta en güçlü etiketi GUCLU olan reddedilen kayıt yok. Kural gevşetilmedi, vaka eklenmedi. |
| `ret_kosullu` | `cal-257109` (ihraç ayı 2015-05) | Eklendi. Karma yol, `min_phi` 0,718, etiket KOSULLU. |

## Ek (δ varsayılanı değişti)
Yukarıdaki sonuç, seçim sırasındaki varsayılan δ = 0,02 içindir ve olduğu gibi kalır. ADR-007 ile
varsayılan δ 0,012 oldu. Aynı kural (aynı 198 kayıt, dosya sırası) yeni varsayılanla yeniden
uygulandığında dağılım GUCLU 4, KOSULLU 27, ZAYIF 6 olur (161 kayıt reddedilen değil ya da planı
yok); ilk GUCLU kayıt `cal-261695`, ilk KOSULLU kayıt `cal-219812`'dir.

Yeniden çalıştırma (ADR-007 sonrası, `/score` varsayılan δ = 0,012, 198 gerçek kayıt, dosya sırası):

| etiket (en güçlü yol) | kayıt sayısı | dosyadaki ilk kayıt |
|---|---|---|
| GUCLU | 4 | `cal-261695` |
| KOSULLU | 27 | `cal-219812` |
| ZAYIF | 6 | - |
| reddedilen değil ya da planı yok | 161 | - |

Mevcut `ret_kosullu` vakası `cal-257109`: tek yol (karma), etiket **KOSULLU**, `min_phi` **0,510**
(δ = 0,02'de 0,718 idi; etiket aynı kaldı).

Karar: GUCLU örnek vakası **eklenmez** ve `ret_kosullu` (`cal-257109`) olduğu gibi kalır; vakalar
seçim anındaki δ ile belirlenmiştir. `ret_kosullu` kaydı yeni varsayılanda da KOSULLU etiketlidir
(testle doğrulanır). Etiket dağılımı δ'ya plan oranından çok daha duyarlıdır (ADR-007).
