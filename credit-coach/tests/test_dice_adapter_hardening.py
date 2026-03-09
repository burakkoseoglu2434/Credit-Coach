from __future__ import annotations

import sys
import time
import types

import numpy as np
import pandas as pd

from credit_coach.recourse.dice_baseline import generate_dice_counterfactual_actions


class DummyModel:
    def predict_proba(self, x):
        n = len(x)
        p = np.full(n, 0.4, dtype=float)
        return np.column_stack([1.0 - p, p])


class _DummyCFExample:
    def __init__(self, df: pd.DataFrame):
        self.final_cfs_df = df


class _DummyCFResult:
    def __init__(self, df: pd.DataFrame):
        self.cf_examples_list = [_DummyCFExample(df)]


def _install_fake_dice(
    monkeypatch,
    *,
    query_arg: str = "query_instance",
    fail_methods: set[str] | None = None,
    sleep_methods: dict[str, float] | None = None,
):
    fail_methods = fail_methods or set()
    sleep_methods = sleep_methods or {}

    class _Data:
        def __init__(self, dataframe, continuous_features, outcome_name):
            self.dataframe = dataframe
            self.continuous_features = continuous_features
            self.outcome_name = outcome_name

    class _Model:
        def __init__(self, model, backend, model_type):
            self.model = model
            self.backend = backend
            self.model_type = model_type

    class _Dice:
        def __init__(self, data, model, method):
            self.data = data
            self.model = model
            self.method = method

        if query_arg == "query_instances":

            def generate_counterfactuals(
                self,
                query_instances,
                total_CFs,
                desired_class,
                features_to_vary,
                random_seed=None,
            ):
                if self.method in fail_methods:
                    raise TypeError(f"method {self.method} failed")
                sleep_s = float(sleep_methods.get(self.method, 0.0))
                if sleep_s > 0:
                    time.sleep(sleep_s)
                df = query_instances.copy()
                if features_to_vary:
                    feat = features_to_vary[0]
                    df[feat] = df[feat].astype(float) * 0.9
                return _DummyCFResult(df)
        else:

            def generate_counterfactuals(
                self,
                query_instance,
                total_CFs,
                desired_class,
                features_to_vary,
                random_seed=None,
            ):
                if self.method in fail_methods:
                    raise TypeError(f"method {self.method} failed")
                sleep_s = float(sleep_methods.get(self.method, 0.0))
                if sleep_s > 0:
                    time.sleep(sleep_s)
                df = query_instance.copy()
                if features_to_vary:
                    feat = features_to_vary[0]
                    df[feat] = df[feat].astype(float) * 0.9
                return _DummyCFResult(df)

    fake_module = types.SimpleNamespace(Data=_Data, Model=_Model, Dice=_Dice)
    monkeypatch.setitem(sys.modules, "dice_ml", fake_module)


def test_dice_invalid_method_falls_back():
    train = pd.DataFrame({"f1": [0.0, 1.0], "f2": [1.0, 0.0], "target": [0, 1]})
    row = train.iloc[1]
    actions, backend, telemetry = generate_dice_counterfactual_actions(
        row=row,
        feature_cols=["f1", "f2"],
        actionable_features=["f1", "f2"],
        model=DummyModel(),
        calibrator=None,
        train_df=train,
        target_col="target",
        dice_method="unsupported",
    )
    assert backend == "heuristic_fallback_invalid_method"
    assert actions and isinstance(actions[0], list)
    assert telemetry["fallback_reason"] == "invalid_method"


def test_dice_method_and_telemetry_with_adapter(monkeypatch):
    _install_fake_dice(monkeypatch)
    train = pd.DataFrame(
        {
            "f1": [0.0, 1.0, 2.0],
            "f2": ["A", "B", "A"],
            "target": [0, 1, 0],
        }
    )
    row = train.iloc[1]
    action_sets, backend, telemetry = generate_dice_counterfactual_actions(
        row=row,
        feature_cols=["f1", "f2"],
        actionable_features=["f1"],
        model=DummyModel(),
        calibrator=None,
        train_df=train,
        target_col="target",
        dice_method="genetic",
        total_cfs=2,
        random_seed=11,
        max_actions=2,
    )

    assert backend == "dice"
    assert len(action_sets) >= 1
    assert telemetry["method_requested"] == "genetic"
    assert telemetry["method_used"] == "genetic"
    assert telemetry["fallback_reason"] is None
    assert telemetry["continuous_feature_count"] == 1
    assert telemetry["categorical_feature_count"] == 1
    assert telemetry["changed_feature_union_count"] >= 1


def test_dice_query_instances_signature_compat(monkeypatch):
    _install_fake_dice(monkeypatch, query_arg="query_instances")
    train = pd.DataFrame({"f1": [0.0, 1.0], "f2": [1.0, 0.0], "target": [0, 1]})
    row = train.iloc[1]
    action_sets, backend, telemetry = generate_dice_counterfactual_actions(
        row=row,
        feature_cols=["f1", "f2"],
        actionable_features=["f1"],
        model=DummyModel(),
        calibrator=None,
        train_df=train,
        target_col="target",
        dice_method="random",
    )
    assert backend == "dice"
    assert action_sets
    assert telemetry["method_used"] == "random"
    assert telemetry["fallback_reason"] is None


def test_dice_falls_forward_to_next_method(monkeypatch):
    _install_fake_dice(monkeypatch, query_arg="query_instance", fail_methods={"random"})
    train = pd.DataFrame({"f1": [0.0, 1.0], "f2": [1.0, 0.0], "target": [0, 1]})
    row = train.iloc[1]
    action_sets, backend, telemetry = generate_dice_counterfactual_actions(
        row=row,
        feature_cols=["f1", "f2"],
        actionable_features=["f1"],
        model=DummyModel(),
        calibrator=None,
        train_df=train,
        target_col="target",
        dice_method="random",
        enable_method_fallback=True,
    )

    assert backend == "dice"
    assert action_sets
    assert telemetry["method_requested"] == "random"
    assert telemetry["method_used"] in {"genetic", "kdtree"}
    assert telemetry["attempted_method_count"] >= 2
    assert telemetry["fallback_reason"] is None


def test_dice_timeout_falls_back(monkeypatch):
    _install_fake_dice(
        monkeypatch,
        query_arg="query_instance",
        sleep_methods={"random": 0.2, "genetic": 0.2, "kdtree": 0.2},
    )
    train = pd.DataFrame({"f1": [0.0, 1.0], "f2": [1.0, 0.0], "target": [0, 1]})
    row = train.iloc[1]
    action_sets, backend, telemetry = generate_dice_counterfactual_actions(
        row=row,
        feature_cols=["f1", "f2"],
        actionable_features=["f1"],
        model=DummyModel(),
        calibrator=None,
        train_df=train,
        target_col="target",
        dice_method="random",
        enable_method_fallback=True,
        timeout_ms=10,
    )

    assert backend == "heuristic_fallback_timeout"
    assert action_sets
    assert telemetry["fallback_reason"] == "timeout"


def test_dice_kdtree_without_random_seed_signature(monkeypatch):
    class _Data:
        def __init__(self, dataframe, continuous_features, outcome_name):
            self.dataframe = dataframe
            self.continuous_features = continuous_features
            self.outcome_name = outcome_name

    class _Model:
        def __init__(self, model, backend, model_type):
            self.model = model
            self.backend = backend
            self.model_type = model_type

    class _Dice:
        def __init__(self, data, model, method):
            self.data = data
            self.model = model
            self.method = method

        # kdtree-like signature that does not accept random_seed.
        def generate_counterfactuals(
            self,
            query_instance,
            total_CFs,
            desired_class,
            features_to_vary,
        ):
            df = query_instance.copy()
            if features_to_vary:
                feat = features_to_vary[0]
                df[feat] = df[feat].astype(float) * 0.9
            return _DummyCFResult(df)

    fake_module = types.SimpleNamespace(Data=_Data, Model=_Model, Dice=_Dice)
    monkeypatch.setitem(sys.modules, "dice_ml", fake_module)

    train = pd.DataFrame({"f1": [0.0, 1.0], "f2": [1.0, 0.0], "target": [0, 1]})
    row = train.iloc[1]
    action_sets, backend, telemetry = generate_dice_counterfactual_actions(
        row=row,
        feature_cols=["f1", "f2"],
        actionable_features=["f1"],
        model=DummyModel(),
        calibrator=None,
        train_df=train,
        target_col="target",
        dice_method="kdtree",
        random_seed=11,
    )

    assert backend == "dice"
    assert action_sets
    assert telemetry["method_used"] == "kdtree"
