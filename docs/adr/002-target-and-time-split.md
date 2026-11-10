# ADR-002: Hedef tanımı ve zamana göre bölme

Durum: kabul edildi

## Bağlam
Eldeki veri 48 sütunluk önceden seçilmiş bir LendingClub alt kümesidir. `loan_status`, ödeme
tarihleri ve vadesi dolmamış kayıt bilgisi yoktur; yalnızca hazır bir `target` (0/1) vardır.
Bu nedenle sabit ufuklu (örn. 12 ay) hedef üretilemez. `target`'ın v1'deki üretim kuralı
doğrulanmadı.

## Karar
1. Hedef: mevcut `target` (1 = kötü sonuç). Etiket kırpılmasını (sağdan sansür) önlemek için
   yalnızca **olgunlaşmış kohort** kullanılır: `term = 36 months` ve `issue_d` 2012-01..2015-12.
   36 aylık kredilerin sonuçları en geç 2018-12'de belli olur, veri 2018-12'de biter.
2. Bölme yalnızca `issue_d` ile yapılır, dilimler arasında en az 2 ay boşluk bırakılır:
   - train: 2012-01 .. 2014-12
   - calibration: 2015-03 .. 2015-06
   - test: 2015-09 .. 2015-12
3. Sınırlar `configs/split.yaml` içindedir; kodda sabit tutulmaz.

## Sonuçlar
- 60 aylık krediler ve 2016 sonrası kayıtlar bu sürümde dışarıdadır.
- Gerçek `loan_status` içeren ham dosya bulunursa ufuk yeniden değerlendirilmelidir.
- Boşluk, komşu aylardaki sonuç örtüşmesini azaltır; tamamen ortadan kaldırmaz.
