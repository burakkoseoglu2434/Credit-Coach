# Reddedilen başvurular ve eğitim desteği: örtüşme

Kaynak: LendingClub reddedilen başvurular 2007-2018Q4 (yol ve sha256: configs/data_source.yaml; sha256 07eb8468d55340d8ca4145c3e3c2e2d3e25ff83c44e432a825729ee6c99c4d45).
Destek: configs/support.yaml (yalnızca eğitim dilimi; içerik hash 0e33e7ddac53aa4dec71f5bc67803381ed8919ccacaf5c0248576d81b2f0e697).
Etiket, model ve test dilimi kullanılmadı.

## Ne demek

- Her oran, reddedilen başvurularda eşlenen bir alanın değerinin eğitim min/max aralığında (kategorikte eğitimde görülen değer kümesinde) olup olmadığının sayımıdır.
- Boş değer ne içeride ne dışarıdadır; paydaya girmez, boş sayısı ayrı verilir.
- Yıl, 'Application Date' alanının yılıdır.

## Ne DEMEK DEĞİL

- Reddin nedeni değildir.
- Modelin bu başvurularda doğru çalışacağı ya da çalışmayacağı anlamına gelmez.
- Çok boyutlu destek değildir; alanlar tek tek aralığa bakar.
- Alan tanımlarının iki dosyada aynı olduğu kanıtlanmadı; 'güven' sütunu eşlemenin durumunu gösterir.
- Kabul edilen başvurularla bir karşılaştırma değildir.

## Alan eşlemesi

| Alan | Reddedilen sütun | Destek özelliği | Tür | Destek aralığı / küme | Güven | Not |
|---|---|---|---|---|---|---|
| dti | Debt-To-Income Ratio | dti | sayisal | 0 - 39.99 | orta | '%' atılır; yüzde ölçeği (0-100). Kabul edilenlerdeki dti ile aynı tanım olduğu doğrulanmadı. |
| risk_skoru | Risk_Score | fico_range_low | sayisal | 660 - 845 | işaretli | Tek puan, destekte ise aralığın alt ucu. Kaynak skor (FICO / Vantage) dosyada belirtilmiyor. EMİN DEĞİLİM. |
| calisma_suresi | Employment Length | emp_length | kategorik | 1 year, 10+ years, 2 years, 3 years, 4 years, 5 years, 6 years, 7 years, 8 years, 9 years, < 1 year | yüksek | Değer kümesi aynı metin kalıbını kullanıyor; boşluk kırpılır. |
| talep_tutari | Amount Requested | loan_amnt | sayisal | 1000 - 35000 | orta | Talep edilen tutar; destekte onaylanan tutar. Aynı büyüklük değil. |
| risk_skoru_alt | Risk_Score | fico_range_high | sayisal | 664 - 850 | işaretli | Duyarlılık satırı: aynı skor, aralığın üst ucuna karşı. Ortak sayıma girmez. |

Eşlenmeyen sütunlar:

- Loan Title: Serbest metin; destekteki 'purpose' kümesiyle eşleşmiyor.
- Zip Code: Destekte karşılığı yok.
- State: Destekte karşılığı yok.
- Policy Code: Destekte karşılığı yok.
- Application Date: Yalnızca yıl bölümü için kullanılır; destek alanı değil.

## Alan başına destek içi / destek dışı

### dti

| Dönem | Başvuru | Boş | Değerlendirilen | Destek içi | Destek dışı | Destek dışı oranı |
|---|---|---|---|---|---|---|
| 2012 | 337,277 | 0 | 337,277 | 285,067 | 52,210 | 15.5% |
| 2013 | 760,942 | 0 | 760,942 | 630,078 | 130,864 | 17.2% |
| 2014 | 1,933,700 | 0 | 1,933,700 | 1,400,669 | 533,031 | 27.6% |
| 2015 | 2,859,379 | 0 | 2,859,379 | 2,080,995 | 778,384 | 27.2% |
| 2012-2015 | 5,891,298 | 0 | 5,891,298 | 4,396,809 | 1,494,489 | 25.4% |
| tümü | 27,648,741 | 0 | 27,648,741 | 20,453,313 | 7,195,428 | 26.0% |

### risk_skoru

| Dönem | Başvuru | Boş | Değerlendirilen | Destek içi | Destek dışı | Destek dışı oranı |
|---|---|---|---|---|---|---|
| 2012 | 337,277 | 4,338 | 332,939 | 133,247 | 199,692 | 60.0% |
| 2013 | 760,942 | 23,822 | 737,120 | 290,273 | 446,847 | 60.6% |
| 2014 | 1,933,700 | 254,523 | 1,679,177 | 591,543 | 1,087,634 | 64.8% |
| 2015 | 2,859,379 | 2,348,928 | 510,451 | 183,799 | 326,652 | 64.0% |
| 2012-2015 | 5,891,298 | 2,631,611 | 3,259,687 | 1,198,862 | 2,060,825 | 63.2% |
| tümü | 27,648,741 | 18,497,630 | 9,151,111 | 3,111,089 | 6,040,022 | 66.0% |

### calisma_suresi

| Dönem | Başvuru | Boş | Değerlendirilen | Destek içi | Destek dışı | Destek dışı oranı |
|---|---|---|---|---|---|---|
| 2012 | 337,277 | 3,584 | 333,693 | 333,693 | 0 | 0.0% |
| 2013 | 760,942 | 11,149 | 749,793 | 749,793 | 0 | 0.0% |
| 2014 | 1,933,700 | 31,781 | 1,901,919 | 1,901,919 | 0 | 0.0% |
| 2015 | 2,859,379 | 73,743 | 2,785,636 | 2,785,636 | 0 | 0.0% |
| 2012-2015 | 5,891,298 | 120,257 | 5,771,041 | 5,771,041 | 0 | 0.0% |
| tümü | 27,648,741 | 951,355 | 26,697,386 | 26,697,386 | 0 | 0.0% |

### talep_tutari

| Dönem | Başvuru | Boş | Değerlendirilen | Destek içi | Destek dışı | Destek dışı oranı |
|---|---|---|---|---|---|---|
| 2012 | 337,277 | 0 | 337,277 | 337,106 | 171 | 0.1% |
| 2013 | 760,942 | 0 | 760,942 | 760,934 | 8 | 0.0% |
| 2014 | 1,933,700 | 0 | 1,933,700 | 1,916,409 | 17,291 | 0.9% |
| 2015 | 2,859,379 | 0 | 2,859,379 | 2,809,628 | 49,751 | 1.7% |
| 2012-2015 | 5,891,298 | 0 | 5,891,298 | 5,824,077 | 67,221 | 1.1% |
| tümü | 27,648,741 | 0 | 27,648,741 | 26,537,638 | 1,111,103 | 4.0% |

### risk_skoru_alt (duyarlılık)

| Dönem | Başvuru | Boş | Değerlendirilen | Destek içi | Destek dışı | Destek dışı oranı |
|---|---|---|---|---|---|---|
| 2012 | 337,277 | 4,338 | 332,939 | 125,192 | 207,747 | 62.4% |
| 2013 | 760,942 | 23,822 | 737,120 | 270,445 | 466,675 | 63.3% |
| 2014 | 1,933,700 | 254,523 | 1,679,177 | 548,787 | 1,130,390 | 67.3% |
| 2015 | 2,859,379 | 2,348,928 | 510,451 | 169,700 | 340,751 | 66.8% |
| 2012-2015 | 5,891,298 | 2,631,611 | 3,259,687 | 1,114,124 | 2,145,563 | 65.8% |
| tümü | 27,648,741 | 18,497,630 | 9,151,111 | 2,879,109 | 6,272,002 | 68.5% |

## Ortak sayım (ana alanlar: dti, risk_skoru, calisma_suresi, talep_tutari)

'En az bir alanda destek dışı': en az bir alanı değerlendirilebilen başvurular içinde. 'Tüm alanlar dolu': dört alanı da dolu olan başvurular içinde.

| Dönem | Başvuru | En az bir alan değerlendirilen | En az bir alanda destek dışı | oran | Tüm alanlar dolu | Bunlardan destek dışı | oran |
|---|---|---|---|---|---|---|---|
| 2012 | 337,277 | 337,277 | 233,029 | 69.1% | 329,356 | 228,695 | 69.4% |
| 2013 | 760,942 | 760,942 | 531,304 | 69.8% | 726,041 | 516,814 | 71.2% |
| 2014 | 1,933,700 | 1,933,700 | 1,454,451 | 75.2% | 1,648,116 | 1,216,901 | 73.8% |
| 2015 | 2,859,379 | 2,859,379 | 1,040,976 | 36.4% | 498,001 | 378,291 | 76.0% |
| 2012-2015 | 5,891,298 | 5,891,298 | 3,259,760 | 55.3% | 3,201,514 | 2,340,701 | 73.1% |
| tümü | 27,648,741 | 27,648,741 | 12,654,551 | 45.8% | 8,992,595 | 6,880,236 | 76.5% |
