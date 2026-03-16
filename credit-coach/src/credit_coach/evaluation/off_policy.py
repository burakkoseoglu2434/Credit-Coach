from __future__ import annotations

from typing import Any

import pandas as pd

CANONICAL_PROXY_METRICS = ("approval_rate", "default_rate_90d", "avg_margin_90d")


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return float(default)
    except Exception:
        pass
    try:
        return float(value)
    except Exception:
        return float(default)


def _ess(weights: pd.Series) -> float:
    if weights.empty:
        return 0.0
    numerator = float(weights.sum()) ** 2
    denominator = float((weights**2).sum())
    if denominator <= 0.0:
        return 0.0
    return float(numerator / denominator)


def _confidence_rank(label: str) -> int:
    return {"strong": 2, "tentative": 1, "degraded": 0}.get(str(label), 0)


def _downgrade_confidence(current: str, candidate: str) -> str:
    return candidate if _confidence_rank(candidate) < _confidence_rank(current) else current


def _metric_reward(df: pd.DataFrame, metric: str) -> tuple[pd.Series, pd.Series]:
    if metric == "approval_rate":
        rewards = pd.to_numeric(df.get("approved", pd.Series(dtype=float)), errors="coerce")
    elif metric == "default_rate_90d":
        rewards = pd.to_numeric(df.get("observed_default_90d", pd.Series(dtype=float)), errors="coerce")
    elif metric == "avg_margin_90d":
        rewards = pd.to_numeric(df.get("observed_margin_90d", pd.Series(dtype=float)), errors="coerce")
    else:
        raise ValueError(f"Unsupported proxy metric: {metric}")
    valid = rewards.notna()
    return rewards, valid


def _metric_label(metric: str, *, delta: float | None, confidence: str) -> str:
    if confidence != "strong" or delta is None:
        return "insufficient_evidence"
    if abs(float(delta)) <= 1e-12:
        return "mixed"
    if metric == "default_rate_90d":
        return "supports_treatment" if float(delta) < 0.0 else "supports_control"
    return "supports_treatment" if float(delta) > 0.0 else "supports_control"


def _overall_policy_signal(labels: list[str]) -> str:
    filtered = [label for label in labels if label != "insufficient_evidence"]
    if not filtered:
        return "insufficient_evidence"
    supports_treatment = any(label == "supports_treatment" for label in filtered)
    supports_control = any(label == "supports_control" for label in filtered)
    if supports_treatment and supports_control:
        return "mixed"
    if supports_treatment:
        return "supports_treatment"
    if supports_control:
        return "supports_control"
    return "mixed"


def _comparison_rank(comparison: dict[str, Any]) -> tuple[float, float, str]:
    score = 0.0
    labels = comparison.get("metric_labels", {})
    if isinstance(labels, dict):
        for label in labels.values():
            if label == "supports_treatment":
                score += 1.0
            elif label == "supports_control":
                score -= 1.0
    mean_confidence = {"strong": 2.0, "tentative": 1.0, "degraded": 0.0}.get(
        str(comparison.get("ope_confidence", "degraded")),
        0.0,
    )
    return (
        float(score),
        float(mean_confidence),
        str(comparison.get("policy_arm", "")),
    )


def evaluate_off_policy(
    learning_df: pd.DataFrame,
    *,
    baseline_arm: str = "control",
) -> dict[str, Any]:
    if learning_df is None or learning_df.empty:
        return {
            "comparison_status": "no_data",
            "ope_confidence": "tentative",
            "baseline_arm": str(baseline_arm),
            "canonical_proxy_metrics": list(CANONICAL_PROXY_METRICS),
            "reward_coverage": {},
            "comparisons": [],
            "preferred_policy_signal": {},
        }

    df = learning_df.copy(deep=True)
    df["policy_arm"] = df.get("policy_arm", "").map(lambda value: str(value or "").strip())
    df["selection_propensity"] = pd.to_numeric(df.get("selection_propensity"), errors="coerce")
    df = df[df["policy_arm"] != ""].reset_index(drop=True)
    if df.empty:
        return {
            "comparison_status": "no_data",
            "ope_confidence": "tentative",
            "baseline_arm": str(baseline_arm),
            "canonical_proxy_metrics": list(CANONICAL_PROXY_METRICS),
            "reward_coverage": {},
            "comparisons": [],
            "preferred_policy_signal": {},
        }

    baseline_rows = df[df["policy_arm"] == str(baseline_arm)]
    if baseline_rows.empty:
        return {
            "comparison_status": "baseline_missing",
            "ope_confidence": "tentative",
            "baseline_arm": str(baseline_arm),
            "canonical_proxy_metrics": list(CANONICAL_PROXY_METRICS),
            "reward_coverage": {
                metric: float(_metric_reward(df, metric)[1].mean())
                for metric in CANONICAL_PROXY_METRICS
            },
            "comparisons": [],
            "preferred_policy_signal": {},
        }

    arms = sorted(str(arm) for arm in df["policy_arm"].dropna().unique().tolist() if str(arm) != str(baseline_arm))
    if not arms:
        return {
            "comparison_status": "control_comparison",
            "ope_confidence": "tentative",
            "baseline_arm": str(baseline_arm),
            "canonical_proxy_metrics": list(CANONICAL_PROXY_METRICS),
            "reward_coverage": {
                metric: float(_metric_reward(df, metric)[1].mean())
                for metric in CANONICAL_PROXY_METRICS
            },
            "comparisons": [],
            "preferred_policy_signal": {},
        }

    policy_profiles = {}
    if "policy_arm_profile" in df.columns:
        for _, row in df[["policy_arm", "policy_arm_profile"]].drop_duplicates(subset=["policy_arm"]).iterrows():
            profile = row["policy_arm_profile"]
            if isinstance(profile, dict):
                policy_profiles[str(row["policy_arm"])] = {
                    str(key): str(value or "")
                    for key, value in profile.items()
                    if str(value or "")
                }

    comparisons: list[dict[str, Any]] = []
    overall_confidence = "strong"
    reward_coverage = {
        metric: float(_metric_reward(df, metric)[1].mean())
        for metric in CANONICAL_PROXY_METRICS
    }
    arm_counts = df["policy_arm"].value_counts(dropna=False).to_dict()
    total_count = int(len(df))
    min_arm_share = float(min((float(count) / max(1, total_count) for count in arm_counts.values()), default=0.0))

    for arm in arms:
        arm_rows = df[df["policy_arm"] == arm]
        arm_prop = pd.to_numeric(arm_rows["selection_propensity"], errors="coerce")
        propensity_coverage = float(arm_prop.notna().mean()) if not arm_rows.empty else 0.0
        valid_prop = arm_prop.fillna(0.0) > 0.0
        arm_confidence = "strong"
        if propensity_coverage < 0.95:
            arm_confidence = _downgrade_confidence(arm_confidence, "degraded")
        if float(min_arm_share) < 0.10:
            arm_confidence = _downgrade_confidence(arm_confidence, "tentative")

        comparison: dict[str, Any] = {
            "policy_arm": arm,
            "policy_arm_profile": policy_profiles.get(arm, {}),
            "baseline_arm": str(baseline_arm),
            "logged_count": int(len(arm_rows)),
            "arm_share": float(len(arm_rows) / max(1, total_count)),
            "propensity_coverage": propensity_coverage,
            "metric_labels": {},
            "metrics": {},
            "ope_confidence": arm_confidence,
        }

        all_labels: list[str] = []
        for metric in CANONICAL_PROXY_METRICS:
            rewards, valid_reward = _metric_reward(df, metric)
            metric_df = df.assign(_reward=rewards, _valid_reward=valid_reward)
            valid_df = metric_df[metric_df["_valid_reward"]].copy()
            metric_confidence = arm_confidence
            if valid_df.empty:
                metric_confidence = _downgrade_confidence(metric_confidence, "degraded")
                metric_payload = {
                    "reward_coverage": 0.0,
                    "baseline_direct_mean": 0.0,
                    "ips_estimate": None,
                    "dr_estimate": None,
                    "ips_delta": None,
                    "dr_delta": None,
                    "effective_sample_size": 0.0,
                }
                label = _metric_label(metric, delta=None, confidence=metric_confidence)
            else:
                reward_coverage_metric = float(valid_df["_valid_reward"].mean())
                if reward_coverage_metric < 0.50:
                    metric_confidence = _downgrade_confidence(metric_confidence, "degraded")
                elif reward_coverage_metric < 0.80:
                    metric_confidence = _downgrade_confidence(metric_confidence, "tentative")

                control_valid = valid_df[valid_df["policy_arm"] == str(baseline_arm)]
                baseline_direct_mean = float(control_valid["_reward"].mean()) if not control_valid.empty else 0.0
                target_valid = valid_df[valid_df["policy_arm"] == arm].copy()
                if target_valid.empty:
                    metric_confidence = _downgrade_confidence(metric_confidence, "degraded")
                    ips_estimate = None
                    dr_estimate = None
                    ess = 0.0
                else:
                    target_valid["_prop"] = pd.to_numeric(target_valid["selection_propensity"], errors="coerce")
                    target_valid = target_valid[target_valid["_prop"].fillna(0.0) > 0.0].copy()
                    if target_valid.empty:
                        metric_confidence = _downgrade_confidence(metric_confidence, "degraded")
                        ips_estimate = None
                        dr_estimate = None
                        ess = 0.0
                    else:
                        weights = 1.0 / target_valid["_prop"].clip(lower=1e-6)
                        ess = _ess(weights)
                        if ess < 10.0:
                            metric_confidence = _downgrade_confidence(metric_confidence, "degraded")
                        elif ess < 30.0:
                            metric_confidence = _downgrade_confidence(metric_confidence, "tentative")

                        ips_estimate = float((weights * target_valid["_reward"]).sum() / max(1, len(valid_df)))
                        reward_by_arm = valid_df.groupby("policy_arm")["_reward"].mean().to_dict()
                        q_target = float(reward_by_arm.get(arm, valid_df["_reward"].mean()))
                        target_valid["_q_logged"] = target_valid["policy_arm"].map(reward_by_arm).astype(float)
                        dr_terms = q_target + (1.0 / target_valid["_prop"].clip(lower=1e-6)) * (
                            target_valid["_reward"] - target_valid["_q_logged"]
                        )
                        direct_component = float(q_target) * max(0, len(valid_df) - len(target_valid))
                        dr_estimate = float((float(dr_terms.sum()) + direct_component) / max(1, len(valid_df)))

                if ips_estimate is None or dr_estimate is None:
                    label = _metric_label(metric, delta=None, confidence=metric_confidence)
                    metric_payload = {
                        "reward_coverage": reward_coverage_metric,
                        "baseline_direct_mean": baseline_direct_mean,
                        "ips_estimate": None,
                        "dr_estimate": None,
                        "ips_delta": None,
                        "dr_delta": None,
                        "effective_sample_size": float(ess if "ess" in locals() else 0.0),
                    }
                else:
                    ips_delta = float(ips_estimate - baseline_direct_mean)
                    dr_delta = float(dr_estimate - baseline_direct_mean)
                    label = _metric_label(metric, delta=dr_delta, confidence=metric_confidence)
                    metric_payload = {
                        "reward_coverage": reward_coverage_metric,
                        "baseline_direct_mean": baseline_direct_mean,
                        "ips_estimate": ips_estimate,
                        "dr_estimate": dr_estimate,
                        "ips_delta": ips_delta,
                        "dr_delta": dr_delta,
                        "effective_sample_size": float(ess),
                    }

            comparison["metrics"][metric] = metric_payload
            comparison["metric_labels"][metric] = label
            all_labels.append(label)
            comparison["ope_confidence"] = _downgrade_confidence(str(comparison["ope_confidence"]), metric_confidence)

        comparison["preferred_policy_signal"] = _overall_policy_signal(all_labels)
        comparisons.append(comparison)
        overall_confidence = _downgrade_confidence(overall_confidence, str(comparison["ope_confidence"]))

    preferred_policy_signal: dict[str, Any] = {}
    if comparisons:
        best = max(comparisons, key=_comparison_rank)
        preferred_policy_signal = {
            "policy_arm": str(best.get("policy_arm", "")),
            "policy_arm_profile": dict(best.get("policy_arm_profile", {})) if isinstance(best.get("policy_arm_profile"), dict) else {},
            "signal": str(best.get("preferred_policy_signal", "insufficient_evidence")),
            "ope_confidence": str(best.get("ope_confidence", "degraded")),
        }

    return {
        "comparison_status": "treatment_vs_control" if "treatment" in arms else "control_comparison",
        "ope_confidence": overall_confidence,
        "baseline_arm": str(baseline_arm),
        "canonical_proxy_metrics": list(CANONICAL_PROXY_METRICS),
        "reward_coverage": reward_coverage,
        "comparisons": comparisons,
        "preferred_policy_signal": preferred_policy_signal,
    }
