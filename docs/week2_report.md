# Hafta 2.5: tek seferlik test raporu

Test dilimi (2015-09..2015-12, 36 ay) 107434 kayıt, gözlenen temerrüt oranı 0.1484. Dondurulmuş paket (bundle.lock.json doğrulandı), git `3f48bcf549`. Test dilimi yalnızca bir kez çalıştırıldı; hiçbir ayar yapılmadı.

| Metrik | Değer |
|---|---|
| Out-of-time AUC (ham model) | 0.6906 |
| AUC (kalibre nokta tahmini) | 0.6903 |
| Brier (ham / kalibre) | 0.1192 / 0.1189 |
| LogLoss (kalibre) | 0.3904 |
| ECE (ham / kalibre) | 0.0149 / 0.0025 |
| Ort. kalibre PD / gözlenen oran | 0.1478 / 0.1484 |
| Aralık genişliği (5/50/95/99. yüzdelik) | 0.0002 / 0.0004 / 0.0026 / 0.0080 |
| Onay eşiği (hurdle 0.11) | 0.1092 |
| Onay oranı | 0.3860 |
| İnsana git oranı | 0.0012 |
| Onay değil oranı | 0.6128 |
| Onaylananlarda gözlenen temerrüt | 0.06770506823552105 |

Beklenti 0,67-0,71 ile karşılaştırma: ham model AUC 0.6906, beklentinin içinde. Nedenine dair tahmin yürütülmedi, yalnızca raporlandı.
