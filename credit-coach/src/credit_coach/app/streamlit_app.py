from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from credit_coach.app.components import metric_card


def _latest_metrics_file() -> Path | None:
    candidates = sorted(Path("artifacts/runs").glob("*/metrics.json"))
    return candidates[-1] if candidates else None


def main() -> None:
    st.set_page_config(page_title="Credit Coach", layout="wide")
    st.title("Credit Coach - Offline Demo")

    metrics_path = _latest_metrics_file()
    if metrics_path is None:
        st.warning("No run metrics found yet.")
        return

    st.caption(f"Latest run metrics: {metrics_path}")
    metric_card("Metrics file", metrics_path.name)

    plans = sorted(Path("artifacts/runs").glob("*/tables/plans.csv"))
    if plans:
        st.subheader("Latest Plans")
        df = pd.read_csv(plans[-1])
        st.dataframe(df.head(20), use_container_width=True)
    else:
        st.info("No plan output yet. Run recourse first.")


if __name__ == "__main__":
    main()
