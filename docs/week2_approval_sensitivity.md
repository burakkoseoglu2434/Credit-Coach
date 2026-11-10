# Hafta 2.4: hurdle duyarlılığı (yalnızca kalibrasyon dilimi, test dilimi kullanılmadı)

Kalibrasyon dilimi 81136 kayıt, genel temerrüt oranı 0.1539. Aralıklar leave-one-month-out. getiri/kayıp: eğitim dilimi ortalamaları (0.1666 / 0.3519). band 0.0027. Seçilen hurdle: 0.11 (onay oranlarına bakılmadan, ADR-003).

|   hurdle |   esik |   onay_orani |   onay_temerrut |   insana_orani |   insana_temerrut |   onay_degil_orani |   onay_degil_temerrut |
|---------:|-------:|-------------:|----------------:|---------------:|------------------:|-------------------:|----------------------:|
|     0.06 | 0.2056 |       0.747  |          0.1138 |         0.005  |            0.1798 |             0.248  |                0.274  |
|     0.09 | 0.1477 |       0.5094 |          0.0866 |         0.0374 |            0.146  |             0.4532 |                0.2301 |
|     0.11 | 0.1092 |       0.3548 |          0.068  |         0.0188 |            0.1323 |             0.6263 |                0.2031 |
|     0.13 | 0.0706 |       0.1639 |          0.0469 |         0.021  |            0.0668 |             0.8151 |                0.1776 |
|     0.15 | 0.032  |       0.01   |          0.016  |         0.0596 |            0.0312 |             0.9304 |                0.1632 |

`*_orani`: tüm başvurular içindeki pay. `*_temerrut`: o gruptaki gözlenen temerrüt oranı.
