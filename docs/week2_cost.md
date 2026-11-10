# Hafta 2.4: maliyet varsayımları ve onay eşiği duyarlılığı

> Etiket: tek fiyatlı kurgusal kredi veren. Bu çalışmadaki kredi veren tek bir sabit getiri, kayıp ve hurdle ile varsayılmıştır; gerçek bir kurumun fiyatlama politikası değildir.

Kaynak: yalnızca eğitim penceresi (2012-01-01..2014-12-01, 36 months), 306462 sonuçlanmış kredi, temerrüt oranı 0.1325. varsayım: eğitim diliminden ampirik, vade ve fon maliyeti dahil değil.

| Büyüklük | Ortalama | Medyan | n |
|---|---|---|---|
| LGD | 0.5030 | 0.5168 | 40596 |
| Sağlam kredi getirisi | 0.1666 | 0.1628 | 265866 |
| Temerrütte tahsil edilen faiz | 0.1511 | 0.1468 | 40596 |
| Temerrüt kaybı (LGD - faiz) | 0.3519 | 0.3567 | 40596 |

Break-even PD* (ortalama): 0.3213, (medyan): 0.3134

## Duyarlılık (ortalama; LGD/kayıp ±%20, getiri ±%20)

|           |   gain x0.8 |   gain x1.0 |   gain x1.2 |
|:----------|------------:|------------:|------------:|
| loss x0.8 |      0.3213 |      0.3718 |      0.4153 |
| loss x1.0 |      0.2747 |      0.3213 |      0.3623 |
| loss x1.2 |      0.2399 |      0.2829 |      0.3213 |

## Duyarlılık (medyan; LGD/kayıp ±%20, getiri ±%20)

|           |   gain x0.8 |   gain x1.0 |   gain x1.2 |
|:----------|------------:|------------:|------------:|
| loss x0.8 |      0.3134 |      0.3633 |      0.4064 |
| loss x1.0 |      0.2675 |      0.3134 |      0.3539 |
| loss x1.2 |      0.2333 |      0.2756 |      0.3134 |
