# Demo v0: geçerli planı olan reddedilenlerin gözlenen temerrüt oranı

> Etiket: tek fiyatlı kurgusal kredi veren. Bu çalışmadaki kredi veren tek bir sabit getiri, kayıp ve hurdle ile varsayılmıştır; gerçek bir kurumun fiyatlama politikası değildir.

Etiketler yalnızca değerlendirme içindir, karar yoluna girmez. Test dilimi yüklenmedi. Reddedilen = v1 REJECTED (destek içi); plan = en az bir yolda geçerli plan (dti güncellemesi kapalı).

Onay eşiği (PD): 0.1092

## Yanında: onaylananların gözlenen oranı

| dilim | onaylanan | gözlenen temerrüt |
|---|---|---|
| kalibrasyon | 28801 | 6.78% |
| boşluk | 34812 | 6.41% |

## Geçerli planı olan reddedilenler: p_point − eşik kovasına göre

| dilim | δ | kova | plan'lı reddedilen | gözlenen temerrüt |
|---|---|---|---|---|
| kalibrasyon | 0 | [0, 0,01) | 3726 | 11.54% |
| kalibrasyon | 0 | [0,01, 0,02) | 3278 | 12.69% |
| kalibrasyon | 0 | [0,02, 0,03) | 2388 | 13.82% |
| kalibrasyon | 0 | [0,03, 0,05) | 3911 | 14.70% |
| kalibrasyon | 0 | [0,05, 0,10) | 1772 | 17.21% |
| kalibrasyon | 0 | [0,10, 0,20) | 425 | 23.29% |
| kalibrasyon | 0 | >= 0,20 | 10 | 30.00% |
| kalibrasyon | 0 | tümü | 15510 | 13.91% |
| kalibrasyon | 0.03 | [0, 0,01) | 1545 | 11.65% |
| kalibrasyon | 0.03 | [0,01, 0,02) | 1000 | 12.90% |
| kalibrasyon | 0.03 | [0,02, 0,03) | 661 | 14.07% |
| kalibrasyon | 0.03 | [0,03, 0,05) | 888 | 15.99% |
| kalibrasyon | 0.03 | [0,05, 0,10) | 342 | 15.20% |
| kalibrasyon | 0.03 | [0,10, 0,20) | 64 | 28.12% |
| kalibrasyon | 0.03 | tümü | 4500 | 13.64% |
| boşluk | 0 | [0, 0,01) | 4477 | 11.46% |
| boşluk | 0 | [0,01, 0,02) | 3803 | 11.36% |
| boşluk | 0 | [0,02, 0,03) | 2708 | 13.74% |
| boşluk | 0 | [0,03, 0,05) | 4433 | 14.73% |
| boşluk | 0 | [0,05, 0,10) | 1904 | 17.07% |
| boşluk | 0 | [0,10, 0,20) | 530 | 19.06% |
| boşluk | 0 | >= 0,20 | 12 | 16.67% |
| boşluk | 0 | tümü | 17867 | 13.42% |
| boşluk | 0.03 | [0, 0,01) | 1916 | 10.96% |
| boşluk | 0.03 | [0,01, 0,02) | 1198 | 10.60% |
| boşluk | 0.03 | [0,02, 0,03) | 720 | 14.17% |
| boşluk | 0.03 | [0,03, 0,05) | 1020 | 13.73% |
| boşluk | 0.03 | [0,05, 0,10) | 363 | 16.80% |
| boşluk | 0.03 | [0,10, 0,20) | 79 | 16.46% |
| boşluk | 0.03 | >= 0,20 | 3 | 0.00% |
| boşluk | 0.03 | tümü | 5299 | 12.32% |
