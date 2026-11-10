# ADR-005: Eylem kataloğu (recourse) v1

Durum: **TASLAK, onay bekliyor.** Kod yok; yalnızca `configs/catalog/v1.yaml` ve bu not.

## Amaç
Reddedilen ya da incelemeye düşen bir müşteri için "ne yaparsan model ilişkisine göre onay eşiğine
yaklaşırsın" planını üreten motorun (4.2-4.6) kullanacağı eylem listesini sabitlemek. Etkiler yalnızca
model üzerinden hesaplanır (kanıt sınıfı M): müşteri metni "ilişkilidir" der, "düşecek" demez.

## Ana bulgu: kısa liste, dürüstçe
İzinli 32 özelliğin çoğu değiştirilemez. Ana sürücüler (FICO, gelir, geçmiş olgular, kayıt geçmişi)
kısa vadede kaldıraç değildir; `int_rate` ve `grade` zaten yasaktır. Kaldıraç olarak kalan dört eylem:
revolving borç kapatma, gecikme kapatma, tahsilat uzlaşması ve kurum karşı teklifi (daha düşük
tutar). Bu yüzden 4. haftada "plan yok" oranının yüksek çıkması beklenir ve bu **dürüst bir sonuçtur**.
Oranı düşürmek için zayıf gerekçeli eylem eklenmez; yeni eylem yalnızca bir gerekçe ve kanıtla girer.

## Model sınırı
Dört eylemin etkilediği özelliklerden yalnızca `revol_util`, `dti`, `acc_now_delinq`, `delinq_amnt`,
`tot_coll_amt` monotondur (+1). `loan_amnt`, `revol_bal`, `tot_cur_bal`, `total_bal_ex_mort` kısıtsızdır:
etki işareti bilinmez. `loan_amnt` için "tutar düşürmek PD'yi düşürür" iddiası savunulamaz (monotone.yaml
gerekçesi). Bu özellikleri içeren dallarda budama yapılmaz (4.3).

## Çok özellikli eylemler (tutarlılık kuralları 5. haftada)
- `revolving_paydown`: revol_util, revol_bal, dti, total_bal_ex_mort, tot_cur_bal birlikte oynar.
- `cure_delinquency`: acc_now_delinq ve delinq_amnt birlikte oynar.
Bu hafta delta kuralları eylemin içinde sabittir; eylemler arası çelişki denetimi 5. haftaya kalır.

## Varsayımlar (hepsi "varsayım" etiketli, ölçülmedi)
- Asgari ödeme oranı 0,02 (dti etkisi), süre aralıkları (hafta), maliyet aralıkları, yürütme olasılıkları.
- Tutar alt sınırı 1000 USD, uzlaşma oranı 0,4-1,0, gecikme ücret payı 1,2.
Yürütme olasılığı bu hafta sıralamada kullanılmaz; yalnızca raporlanır.

## Sahip ve yol türü (4.4 için)
`customer`: revolving_paydown, cure_delinquency, settle_collections. `institution`:
counteroffer_lower_amount. Yol türü sahip kümesinden türetilir: yalnızca customer, hybrid, yalnızca
institution (`institution_assisted`).

## Kapsam dışı (bilinçli)
Dayanıklılık, DAG özdeşlikleri, likidite koruması (5. hafta); ortak başvuru; ürün/vade değişikliği.
