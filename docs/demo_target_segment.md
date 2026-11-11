# Demo v0: hedef segment (p_point − eşik kovasına göre en güçlü yol etiketi)

> Etiket: tek fiyatlı kurgusal kredi veren. Bu çalışmadaki kredi veren tek bir sabit getiri, kayıp ve hurdle ile varsayılmıştır; gerçek bir kurumun fiyatlama politikası değildir.

Kapsam: kalibrasyon dilimi (2015-03..06) ve boşluk ayları (2015-01, 02, 07, 08); test dilimi kullanılmadı. Reddedilen = v1 REJECTED (destek içi). dti güncellemesi kapalı. Eşik 0.1092, band 0.0027. Etiket = kaydın planı olan yolları içinde en güçlü olanı.

## 1. Kovaya göre en güçlü yol etiketi

| dilim | δ | kova (p_point − eşik) | reddedilen | PLAN_YOK | GUCLU | KOSULLU | ZAYIF |
|---|---|---|---|---|---|---|---|
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0, 0,01) | 3943 | 5.5% | 34.6% | 59.9% | 0.0% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0,01, 0,02) | 3855 | 15.0% | 27.3% | 9.2% | 48.5% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0,02, 0,03) | 3529 | 32.3% | 2.1% | 20.5% | 45.1% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0,03, 0,05) | 9757 | 59.9% | 0.0% | 11.3% | 28.7% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0,05, 0,10) | 11171 | 84.1% | 0.0% | 0.3% | 15.6% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0,10, 0,20) | 14143 | 97.0% | 0.0% | 0.0% | 3.0% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | >= 0,20 | 5831 | 99.8% | 0.0% | 0.0% | 0.2% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | tümü | 52229 | 70.3% | 4.8% | 8.8% | 16.2% |
| kalibrasyon | δ = 0,03 | [0, 0,01) | 3943 | 60.8% | 0.0% | 3.9% | 35.3% |
| kalibrasyon | δ = 0,03 | [0,01, 0,02) | 3855 | 74.1% | 0.0% | 2.0% | 24.0% |
| kalibrasyon | δ = 0,03 | [0,02, 0,03) | 3529 | 81.3% | 0.0% | 0.0% | 18.7% |
| kalibrasyon | δ = 0,03 | [0,03, 0,05) | 9757 | 90.9% | 0.0% | 0.0% | 9.1% |
| kalibrasyon | δ = 0,03 | [0,05, 0,10) | 11171 | 96.9% | 0.0% | 0.0% | 3.1% |
| kalibrasyon | δ = 0,03 | [0,10, 0,20) | 14143 | 99.5% | 0.0% | 0.0% | 0.5% |
| kalibrasyon | δ = 0,03 | >= 0,20 | 5831 | 100.0% | 0.0% | 0.0% | 0.0% |
| kalibrasyon | δ = 0,03 | tümü | 52229 | 91.4% | 0.0% | 0.4% | 8.2% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0, 0,01) | 4714 | 5.0% | 34.5% | 60.5% | 0.0% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0,01, 0,02) | 4526 | 16.0% | 27.5% | 7.8% | 48.7% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0,02, 0,03) | 4047 | 33.1% | 2.6% | 19.4% | 44.9% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0,03, 0,05) | 11067 | 59.9% | 0.1% | 11.1% | 28.9% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0,05, 0,10) | 12809 | 85.1% | 0.0% | 0.3% | 14.6% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0,10, 0,20) | 15908 | 96.7% | 0.0% | 0.0% | 3.3% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | >= 0,20 | 6458 | 99.8% | 0.0% | 0.0% | 0.2% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | tümü | 59529 | 70.0% | 5.0% | 8.8% | 16.2% |
| boşluk | δ = 0,03 | [0, 0,01) | 4714 | 59.4% | 0.0% | 4.1% | 36.5% |
| boşluk | δ = 0,03 | [0,01, 0,02) | 4526 | 73.5% | 0.0% | 2.9% | 23.6% |
| boşluk | δ = 0,03 | [0,02, 0,03) | 4047 | 82.2% | 0.0% | 0.0% | 17.8% |
| boşluk | δ = 0,03 | [0,03, 0,05) | 11067 | 90.8% | 0.0% | 0.0% | 9.2% |
| boşluk | δ = 0,03 | [0,05, 0,10) | 12809 | 97.2% | 0.0% | 0.0% | 2.8% |
| boşluk | δ = 0,03 | [0,10, 0,20) | 15908 | 99.5% | 0.0% | 0.0% | 0.5% |
| boşluk | δ = 0,03 | >= 0,20 | 6458 | 100.0% | 0.0% | 0.0% | 0.0% |
| boşluk | δ = 0,03 | tümü | 59529 | 91.1% | 0.0% | 0.5% | 8.4% |

> **Bu tablo ne demek:** Modelin bugünkü risk tahmininin eşiğe uzaklığına göre, reddedilen kayıtların hangi payında hiç plan çıkmadığı (PLAN_YOK) ve planı olanlarda en güçlü yolun etiketi.

> **Ne DEMEK DEĞİL:** Kova bir hedef kitle ya da öncelik önerisi değildir; etiket planın gerçekte işe yarayacağını söylemez, gerçek etki payı bilinmiyor.

## 2. Varsayılan δ: API ve arayüz

| öğe | değer / durum |
|---|---|
| Varsayılan δ | 0.02 (etiket: varsayım: dönem kayması ve model belirsizliği payı; Venn-Abers aralığı değil) |
| Tanımlandığı yer | `configs/catalog/demo_v0.yaml`, `delta.deger`; `bundle.lock.json` bu dosyanın hash'ini taşır |
| API'nin kullandığı değer | `/score` ve `/batch`, `sec_from_scores` çağrısına δ vermez; motor katalogdaki varsayılanı kullanır (`recourse.sec`, `delta=None`) |
| API yanıtında görünür mü | hayır (yanıt ve istek şemasında δ alanı yok); dolaylı iz: `surumler.katalog_sha256` |
| Arayüzde görünür mü | hayır (arayüz δ değerini göstermez; metinlerde yalnızca "güvenli payla" ifadesi geçer) |
| Bu raporun sütunları | δ = 0 (etkin kesim eşik − band) ve δ = 0,03; varsayılan 0,02 ayrı sütun değildir |

> **Bu tablo ne demek:** API ve arayüzün plan ararken hangi δ'yı kullandığı ve bu değerin nerede görünür olduğu; değerler canlı dosyalardan okundu.

> **Ne DEMEK DEĞİL:** Varsayılan δ bu raporun sütunlarından biri değildir; δ ölçülmüş bir büyüklük değil, varsayımdır ve değiştirilmedi.

