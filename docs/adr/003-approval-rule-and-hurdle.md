# ADR-003: Onay eşiği, hurdle ve aralık kuralı

Durum: taslak. Hurdle değerleri henüz verilmedi; bu belge onay oranları görülmeden ÖNCE
yazıldı ve değerler eklendiğinde ayrı bir commit ile tamamlanacak.

## Sıra taahhüdü
1. Hurdle bileşenleri (marj, fon maliyeti, işletme gideri) ve gerekçeleri bu belgeye yazılır,
   commit edilir.
2. Ancak ondan sonra kalibrasyon dilimindeki onay oranları ve onaylananlardaki temerrüt
   oranları hesaplanır. Hurdle, onay oranına bakılarak seçilmez ve sonradan değiştirilmez.
3. Test dilimine 2.5'e kadar bakılmaz.

## Onay kuralı
Beklenen kâr / funded_amnt, kredi ömrü boyunca toplam:

    (1 - PD) * getiri - PD * kayıp  >=  hurdle,   hurdle = asgari_marj + fon_maliyeti + isletme_gideri

- `getiri` = tam ödenen kredilerde total_rec_int / funded_amnt, `kayıp` = temerrüt kaybı
  (LGD - tahsil edilen faiz). İkisi de `configs/cost.yaml` içinde, eğitim diliminden, ortalama.
- Eşik çözümsel: `PD* = (getiri - hurdle) / (getiri + kayıp)`, [0, 1] aralığına kırpılır.
  hurdle = 0 iken break-even PD'ye iner. `getiri <= hurdle` ise hiç kimse onaylanmaz.
- Birim: funded_amnt'ın oranı, 36 aylık toplam (yıllıklandırılmış değil). Fon maliyeti ve işletme
  gideri aynı tabanda verilmelidir.
- Üç hurdle alanı `cost.yaml` içinde "varsayım" etiketlidir, değerleri ve dış kaynak gerekçesi
  kullanıcıdan alınır; uydurulmaz.

## Aralık kuralı
Karar girdisi PD aralığı `[p_low, p_high]` (Venn-Abers).
- Aralık, her iki yanda `band` kadar genişletildiğinde eşiği içeriyorsa: `insana_git`.
  (Eşiği kesen her aralık bu kapsamdadır.)
- Ham skor zayıf destek ondalıklarından birindeyse: `insana_git`.
- Aksi halde `p_high < eşik` ise `onay`, değilse `onay_degil`. Ret eşiği 4. haftada tanımlanır.

### Bant genişliği (hurdle'dan bağımsız, kalibrasyon dilimi)
`band` = kalibrasyon dilimindeki aylık kaymanın en büyük mutlak değeri: her ay için
|ortalama kalibre PD - gözlenen temerrüt oranı| (leave-one-month-out ile). Aylık kayma, hurdle
veya onay oranına bakılmadan hesaplanır.

### Zayıf destek ondalıkları
Kalibrasyon dilimi ham skor ondalıklarında ortalama aralık genişliği, ondalık medyanının 2
katını aşanlar (2.3 raporundaki kural). Skor aralıkları `configs/decision.yaml` içine yazılır.

## Paket kilidi
`bundle.lock.json`: model, kalibratör verisi, `cost.yaml`, `decision.yaml`, özellik manifestosu,
`split.yaml` ve `monotone.yaml` dosyalarının SHA-256 özetleri. Özet değişirse CI düşer; değişiklik
bilinçliyse kilit yeniden yazılır ve commit'e girer.
