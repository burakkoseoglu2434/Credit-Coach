# Hafta 2.2: doğrulama raporu (test dilimi kullanılmadı)

- Ayar: yalnızca train içi zaman doğrulaması (fit ≤ 2014-03, dev ≥ 2014-07), seed 42
- Seçilen (monoton): {"max_depth": 5, "n_estimators": 600, "min_child_weight": 50}
- Seçilen (kısıtsız): {"max_depth": 5, "n_estimators": 300, "min_child_weight": 50}

| Model | Kalibrasyon AUC | Brier | LogLoss |
|---|---|---|---|
| Monoton XGBoost | 0.6844 | 0.1232 | 0.4022 |
| Kısıtsız XGBoost | 0.6843 | 0.1231 | 0.4019 |

Kısıtın maliyeti (kısıtsız AUC - monoton AUC): -0.0001

Monotonluk ihlali veren özellik: yok

## Izgara (iç doğrulama AUC)

- mono {'max_depth': 3, 'n_estimators': 300, 'min_child_weight': 50, 'inner_auc': 0.6746061020127868}
- mono {'max_depth': 3, 'n_estimators': 300, 'min_child_weight': 300, 'inner_auc': 0.6733771806528304}
- mono {'max_depth': 3, 'n_estimators': 600, 'min_child_weight': 50, 'inner_auc': 0.6771762629112318}
- mono {'max_depth': 3, 'n_estimators': 600, 'min_child_weight': 300, 'inner_auc': 0.67616433407762}
- mono {'max_depth': 5, 'n_estimators': 300, 'min_child_weight': 50, 'inner_auc': 0.6773819711615691}
- mono {'max_depth': 5, 'n_estimators': 300, 'min_child_weight': 300, 'inner_auc': 0.6763613302584656}
- mono {'max_depth': 5, 'n_estimators': 600, 'min_child_weight': 50, 'inner_auc': 0.677838261722515}
- mono {'max_depth': 5, 'n_estimators': 600, 'min_child_weight': 300, 'inner_auc': 0.6774726369233117}
- unc {'max_depth': 3, 'n_estimators': 300, 'min_child_weight': 50, 'inner_auc': 0.6756485946234659}
- unc {'max_depth': 3, 'n_estimators': 300, 'min_child_weight': 300, 'inner_auc': 0.6748033843290175}
- unc {'max_depth': 3, 'n_estimators': 600, 'min_child_weight': 50, 'inner_auc': 0.6781565848285999}
- unc {'max_depth': 3, 'n_estimators': 600, 'min_child_weight': 300, 'inner_auc': 0.6772139313797148}
- unc {'max_depth': 5, 'n_estimators': 300, 'min_child_weight': 50, 'inner_auc': 0.6791774270304568}
- unc {'max_depth': 5, 'n_estimators': 300, 'min_child_weight': 300, 'inner_auc': 0.6779588366638822}
- unc {'max_depth': 5, 'n_estimators': 600, 'min_child_weight': 50, 'inner_auc': 0.6788339817395425}
- unc {'max_depth': 5, 'n_estimators': 600, 'min_child_weight': 300, 'inner_auc': 0.6788336539388292}
