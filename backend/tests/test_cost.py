import pandas as pd
import pytest

from credit_coach.cost import COST_COLUMNS, break_even_pd, cost_stats, sensitivity
from credit_coach.features import allowed_features


def _df():
    return pd.DataFrame(
        {
            "funded_amnt": [1000.0, 1000.0, 1000.0, 2000.0],
            "total_rec_prncp": [1000.0, 1000.0, 400.0, 1000.0],
            "total_rec_int": [100.0, 200.0, 50.0, 100.0],
            "recoveries": [0.0, 0.0, 100.0, 0.0],
            "loan_status": ["Fully Paid", "Fully Paid", "Charged Off", "Default"],
        }
    )


def test_cost_stats_formulas():
    s = cost_stats(_df())
    # LGD: (1000-400-100)/1000 = 0.5 ; (2000-1000-0)/2000 = 0.5
    assert s["lgd"]["mean"] == pytest.approx(0.5)
    # yield: 0.1 and 0.2 -> mean 0.15
    assert s["yield_good"]["mean"] == pytest.approx(0.15)
    # interest on defaults: 0.05 and 0.05
    assert s["interest_on_defaults"]["mean"] == pytest.approx(0.05)
    assert s["default_net_loss"]["mean"] == pytest.approx(0.45)
    assert s["bad_rate"] == pytest.approx(0.5)


def test_break_even_formula():
    assert break_even_pd(0.15, 0.45) == pytest.approx(0.25)
    with pytest.raises(ValueError):
        break_even_pd(0.0, 0.4)


def test_sensitivity_is_monotone_in_gain_and_loss():
    t = sensitivity(0.15, 0.45)
    assert t.shape == (3, 3)
    assert (t.diff(axis=1).dropna(axis=1) > 0).all().all()  # more gain -> higher threshold
    assert (t.diff(axis=0).dropna() < 0).all().all()  # more loss -> lower threshold
    assert t.loc["loss x1.0", "gain x1.0"] == pytest.approx(break_even_pd(0.15, 0.45))


def test_cost_columns_are_never_model_features():
    assert not set(COST_COLUMNS) & set(allowed_features())


def test_cost_yaml_is_labelled_and_consistent():
    import yaml

    from credit_coach.features import MANIFEST_PATH

    path = MANIFEST_PATH.parent / "cost.yaml"
    text = path.read_text()
    assert "MODEL GİRDİSİ DEĞİLDİR" in text
    doc = yaml.safe_load(text)
    for key in ("lgd", "saglam_kredi_getirisi", "temerrutte_tahsil_edilen_faiz", "temerrut_kaybi"):
        assert "varsayım" in doc[key]["etiket"] and "fon maliyeti dahil değil" in doc[key]["etiket"]
    gain, loss = doc["saglam_kredi_getirisi"]["mean"], doc["temerrut_kaybi"]["mean"]
    assert doc["onay_esigi_referans"]["break_even_pd_mean"] == pytest.approx(
        break_even_pd(gain, loss)
    )
    assert doc["temerrut_kaybi"]["mean"] == pytest.approx(
        doc["lgd"]["mean"] - doc["temerrutte_tahsil_edilen_faiz"]["mean"]
    )
    assert doc["ret_esigi"] is None


def test_hurdle_fields_exist_and_are_labelled_assumptions():
    import yaml

    from credit_coach.features import MANIFEST_PATH

    doc = yaml.safe_load((MANIFEST_PATH.parent / "cost.yaml").read_text())
    for key in ("asgari_marj", "fon_maliyeti", "isletme_gideri"):
        assert "varsayım" in doc["hurdle"][key]["etiket"]
        assert "deger" in doc["hurdle"][key] and "gerekce" in doc["hurdle"][key]


def test_hurdle_values_total_011():
    from credit_coach.decision import load_cost, total_hurdle

    doc = load_cost()
    assert total_hurdle(doc) == pytest.approx(0.11)
    assert doc["hurdle"]["fon_maliyeti"]["deger"] == pytest.approx(0.05)
    assert 0.03 * 0.55 * 3 == pytest.approx(0.0495)  # documented derivation of fon_maliyeti
    for key in ("asgari_marj", "fon_maliyeti", "isletme_gideri"):
        assert doc["hurdle"][key]["gerekce"].strip()
