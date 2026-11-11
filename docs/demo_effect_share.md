# Demo v0: etki payı duyarlılık eğrisi

> Etiket: tek fiyatlı kurgusal kredi veren. Bu çalışmadaki kredi veren tek bir sabit getiri, kayıp ve hurdle ile varsayılmıştır; gerçek bir kurumun fiyatlama politikası değildir.

Kapsam: kalibrasyon dilimi (2015-03..06) ve boşluk ayları (2015-01, 02, 07, 08); test dilimi kullanılmadı. Reddedilen = v1 REJECTED (destek içi). dti güncellemesi kapalı.

Tanım: model içi plan etkisi Δ = p_önce − p_sonra_model (ikisi de p_high). Gerçek etki payı φ için p_sonra_gerçek = p_önce − φ·Δ. Plan, p_sonra_gerçek < eşik − δ olduğunda geçerli sayılır; eşik 0.1092, band 0.0027. δ = 0'da etkin kesim eşik − band'dır (karar kuralı R2). φ = 1,00 motorun mevcut sonucuyla aynıdır.

## 1. Geçerli planı olan reddedilen oranı, etki payı φ'ye göre

| dilim | δ | φ | reddedilen | en az bir yolda plan | müşteri | karma | kurum |
|---|---|---|---|---|---|---|---|
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | 0,25 | 52229 | 2.0% | 0.3% | 1.7% | 0.7% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | 0,50 | 52229 | 11.3% | 2.8% | 9.0% | 6.0% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | 0,75 | 52229 | 19.3% | 6.0% | 15.5% | 11.0% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | 1,00 | 52229 | 29.7% | 8.7% | 23.7% | 16.8% |
| kalibrasyon | δ = 0,03 | 0,25 | 52229 | 0.0% | 0.0% | 0.0% | 0.0% |
| kalibrasyon | δ = 0,03 | 0,50 | 52229 | 0.1% | 0.0% | 0.1% | 0.0% |
| kalibrasyon | δ = 0,03 | 0,75 | 52229 | 1.7% | 0.2% | 1.5% | 0.3% |
| kalibrasyon | δ = 0,03 | 1,00 | 52229 | 8.6% | 1.4% | 7.6% | 2.5% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | 0,25 | 59529 | 2.1% | 0.4% | 1.8% | 0.7% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | 0,50 | 59529 | 11.6% | 2.9% | 9.3% | 6.3% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | 0,75 | 59529 | 19.8% | 6.2% | 15.8% | 11.5% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | 1,00 | 59529 | 30.0% | 9.1% | 23.9% | 17.2% |
| boşluk | δ = 0,03 | 0,25 | 59529 | 0.0% | 0.0% | 0.0% | 0.0% |
| boşluk | δ = 0,03 | 0,50 | 59529 | 0.1% | 0.0% | 0.1% | 0.0% |
| boşluk | δ = 0,03 | 0,75 | 59529 | 1.9% | 0.2% | 1.7% | 0.4% |
| boşluk | δ = 0,03 | 1,00 | 59529 | 8.9% | 1.5% | 7.8% | 2.7% |

> **Bu tablo ne demek:** Modelin öngördüğü risk düşüşünün yalnızca φ kadarı gerçekleşseydi, hâlâ eşiğin (δ ile) altına inen planı olan reddedilen payı. φ = 1,00 satırı motorun sonucudur.

> **Ne DEMEK DEĞİL:** φ gerçek etkinin ölçüsü değildir; gerçek etki doğrulanmadı ve φ'nin hangi değerde olduğu bilinmiyor. Bir satır, o etki payında planın işe yarayacağını söylemez.

## 2. Geçerli plan oranı, p_point − eşik kovasına ve φ'ye göre

| dilim | δ | kova (p_point − eşik) | reddedilen | φ = 0,25 | φ = 0,50 | φ = 0,75 | φ = 1,00 |
|---|---|---|---|---|---|---|---|
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0, 0,01) | 3943 | 26.1% | 76.4% | 94.5% | 94.5% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0,01, 0,02) | 3855 | 0.5% | 58.0% | 63.7% | 85.0% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0,02, 0,03) | 3529 | 0.0% | 14.8% | 41.2% | 67.7% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0,03, 0,05) | 9757 | 0.0% | 1.2% | 22.4% | 40.1% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0,05, 0,10) | 11171 | 0.0% | 0.0% | 2.4% | 15.9% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0,10, 0,20) | 14143 | 0.0% | 0.0% | 0.1% | 3.0% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | >= 0,20 | 5831 | 0.0% | 0.0% | 0.0% | 0.2% |
| kalibrasyon | δ = 0,03 | [0, 0,01) | 3943 | 0.0% | 0.9% | 13.4% | 39.2% |
| kalibrasyon | δ = 0,03 | [0,01, 0,02) | 3855 | 0.0% | 0.0% | 7.6% | 25.9% |
| kalibrasyon | δ = 0,03 | [0,02, 0,03) | 3529 | 0.0% | 0.0% | 0.7% | 18.7% |
| kalibrasyon | δ = 0,03 | [0,03, 0,05) | 9757 | 0.0% | 0.0% | 0.2% | 9.1% |
| kalibrasyon | δ = 0,03 | [0,05, 0,10) | 11171 | 0.0% | 0.0% | 0.0% | 3.1% |
| kalibrasyon | δ = 0,03 | [0,10, 0,20) | 14143 | 0.0% | 0.0% | 0.0% | 0.5% |
| kalibrasyon | δ = 0,03 | >= 0,20 | 5831 | 0.0% | 0.0% | 0.0% | 0.0% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0, 0,01) | 4714 | 26.1% | 76.6% | 95.0% | 95.0% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0,01, 0,02) | 4526 | 0.5% | 57.2% | 63.4% | 84.0% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0,02, 0,03) | 4047 | 0.0% | 14.2% | 41.1% | 66.9% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0,03, 0,05) | 11067 | 0.0% | 1.5% | 22.6% | 40.1% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0,05, 0,10) | 12809 | 0.0% | 0.0% | 2.2% | 14.9% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0,10, 0,20) | 15908 | 0.0% | 0.0% | 0.1% | 3.3% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | >= 0,20 | 6458 | 0.0% | 0.0% | 0.0% | 0.2% |
| boşluk | δ = 0,03 | [0, 0,01) | 4714 | 0.0% | 1.0% | 13.8% | 40.6% |
| boşluk | δ = 0,03 | [0,01, 0,02) | 4526 | 0.0% | 0.0% | 8.5% | 26.5% |
| boşluk | δ = 0,03 | [0,02, 0,03) | 4047 | 0.0% | 0.0% | 1.0% | 17.8% |
| boşluk | δ = 0,03 | [0,03, 0,05) | 11067 | 0.0% | 0.0% | 0.4% | 9.2% |
| boşluk | δ = 0,03 | [0,05, 0,10) | 12809 | 0.0% | 0.0% | 0.0% | 2.8% |
| boşluk | δ = 0,03 | [0,10, 0,20) | 15908 | 0.0% | 0.0% | 0.0% | 0.5% |
| boşluk | δ = 0,03 | >= 0,20 | 6458 | 0.0% | 0.0% | 0.0% | 0.0% |

> **Bu tablo ne demek:** Eşiğe uzaklık ve etki payı birlikte değiştiğinde planı olan kayıt payı.

> **Ne DEMEK DEĞİL:** Kova, ne kadar çaba gerektiğini ölçmez; yalnızca modelin bugünkü risk tahmininin eşiğe uzaklığıdır.

## 3. Planın geçerli olması için gereken minimum etki payı φ

| dilim | δ | reddedilen | φ = 1,00'de plan var | φ = 1,00'de plan yok | %5 | %25 | %50 | %75 | %95 | ortalama |
|---|---|---|---|---|---|---|---|---|---|---|
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | 52229 | 15510 (29.7%) | 36719 (70.3%) | 0,21 | 0,42 | 0,62 | 0,82 | 0,93 | 0,60 |
| kalibrasyon | δ = 0,03 | 52229 | 4500 (8.6%) | 47729 (91.4%) | 0,67 | 0,79 | 0,87 | 0,98 | 0,99 | 0,86 |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | 59529 | 17867 (30.0%) | 41662 (70.0%) | 0,21 | 0,38 | 0,61 | 0,82 | 0,93 | 0,60 |
| boşluk | δ = 0,03 | 59529 | 5299 (8.9%) | 54230 (91.1%) | 0,67 | 0,78 | 0,86 | 0,98 | 0,99 | 0,86 |

Yol türüne göre medyan gereken φ (yalnızca o yolda planı olan kayıtlar):

| dilim | δ | müşteri | karma | kurum |
|---|---|---|---|---|
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | 0,63 (n=4558) | 0,62 (n=12389) | 0,63 (n=8779) |
| kalibrasyon | δ = 0,03 | 0,89 (n=712) | 0,86 (n=3957) | 0,92 (n=1297) |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | 0,63 (n=5401) | 0,61 (n=14211) | 0,63 (n=10264) |
| boşluk | δ = 0,03 | 0,88 (n=876) | 0,86 (n=4631) | 0,88 (n=1607) |

> **Bu tablo ne demek:** Her reddedilen kayıt için, en az bir planının eşiğin (δ ile) altına inmesi için modelin öngördüğü düşüşün en az hangi kesrinin gerçekleşmesi gerektiği; dağılım bu kesirlerin yüzdelikleridir. φ = 1,00'de bile planı olmayan kayıtlar ayrı sayılır.

> **Ne DEMEK DEĞİL:** Düşük bir değer, planın gerçekte işe yarayacağı anlamına gelmez; yalnızca eşiğe uzaklığın modelin öngördüğü düşüşe oranıdır. Gereken φ'nin altında kalan gerçek etki planı geçersiz kılar, ama gerçek etkinin ne olduğu bu raporda bilinmiyor.

