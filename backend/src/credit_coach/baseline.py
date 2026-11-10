"""Week 2.1: fit LR and unconstrained XGBoost on train, validate on calibration. No test split."""

import pandas as pd

from credit_coach.features import MANIFEST_PATH
from credit_coach.modeling import (
    dev_frame,
    logistic_baseline,
    metrics,
    split_xy,
    unconstrained_xgb,
)

CSV = (
    MANIFEST_PATH.parents[1]
    / "credit-coach/data/lending_club/lending_club_48_features_20251026_114053.csv"
)


def main() -> None:
    dev = dev_frame(pd.read_csv(CSV))
    X_tr, y_tr, X_ca, y_ca = split_xy(dev)
    print(f"train {len(X_tr)} cal {len(X_ca)} features {X_tr.shape[1]}")
    for name, m in (("logistic", logistic_baseline()), ("xgb_unconstrained", unconstrained_xgb())):
        m.fit(X_tr, y_tr)
        print(name, "train", metrics(m, X_tr, y_tr))
        print(name, "cal  ", metrics(m, X_ca, y_ca))


if __name__ == "__main__":
    main()
