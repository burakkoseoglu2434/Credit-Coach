"""Uplift yardımcıları (docs/ecom/PLAN.md bölüm 2-3): bölme, iki model ailesi, metrikler.

Hepsi deterministiktir: sabit seed, sabit random_state, eşitlikler satır kimliğiyle bozulur.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

SEED = 20261111
FRACS = (0.6, 0.2, 0.2)
TRAIN, VALID, TEST = 0, 1, 2
N_POINTS = 100


# --- bölme -------------------------------------------------------------------------------------


def stratified_split(strata: np.ndarray, seed: int = SEED, fracs=FRACS) -> np.ndarray:
    """Her tabakada satır kimlikleri (dosya sırası) seed'li permütasyonla 0,6/0,2/0,2 bölünür."""
    rng = np.random.default_rng(seed)
    labels = np.full(len(strata), -1, dtype=np.int8)
    for s in np.unique(strata):
        idx = np.flatnonzero(strata == s)
        perm = rng.permutation(idx)
        n_tr = int(round(fracs[0] * len(idx)))
        n_va = int(round(fracs[1] * len(idx)))
        labels[perm[:n_tr]] = TRAIN
        labels[perm[n_tr : n_tr + n_va]] = VALID
        labels[perm[n_tr + n_va :]] = TEST
    return labels


def split_hash(labels: np.ndarray) -> str:
    """Bölme karması: satır sırasındaki etiket dizisinin (int8) SHA-256'sı."""
    return hashlib.sha256(np.ascontiguousarray(labels, dtype=np.int8).tobytes()).hexdigest()


# --- modeller ----------------------------------------------------------------------------------


@dataclass(frozen=True)
class Config:
    aile: str  # "T" (iki modelli) ya da "TO" (dönüştürülmüş sonuç)
    learning_rate: float
    max_leaf_nodes: int
    max_iter: int = 200

    @property
    def ad(self) -> str:
        return f"{self.aile}_lr{self.learning_rate}_leaf{self.max_leaf_nodes}_it{self.max_iter}"


def grid() -> list[Config]:
    """Toplam 12 kombinasyon: 2 aile × öğrenme hızı {0,05; 0,1} × yaprak {7, 15, 31}."""
    return [Config(a, lr, leaf) for a in ("T", "TO") for lr in (0.05, 0.1) for leaf in (7, 15, 31)]


def _params(cfg: Config) -> dict:
    return {
        "learning_rate": cfg.learning_rate,
        "max_leaf_nodes": cfg.max_leaf_nodes,
        "max_iter": cfg.max_iter,
        "early_stopping": False,
        "random_state": SEED,
    }


def fit_predict_tau(
    cfg: Config,
    x_tr: np.ndarray,
    y_tr: np.ndarray,
    t_tr: np.ndarray,
    p: float,
    x_ev: np.ndarray,
    binary: bool,
) -> np.ndarray:
    """Eğitimde öğrenir, x_ev için tahmini farkı (tau) döndürür.

    T: her kolda ayrı model, tau = mu1 - mu0 (ikili sonuçta sınıflandırıcı olasılığı).
    TO: Z = Y (T - p) / (p (1 - p)) hedefli tek regresyon; E[Z | X] = tau(X).
    """
    if cfg.aile == "T":
        est = HistGradientBoostingClassifier if binary else HistGradientBoostingRegressor
        mus = []
        for arm in (1, 0):
            m = est(**_params(cfg)).fit(x_tr[t_tr == arm], y_tr[t_tr == arm])
            mus.append(m.predict_proba(x_ev)[:, 1] if binary else m.predict(x_ev))
        return mus[0] - mus[1]
    if cfg.aile == "TO":
        z = y_tr * (t_tr - p) / (p * (1 - p))
        return HistGradientBoostingRegressor(**_params(cfg)).fit(x_tr, z).predict(x_ev)
    raise ValueError(cfg.aile)


# --- metrikler (ağırlıklı: bootstrap çokluk ağırlığı; ağırlık 1 = ham) -------------------------


def rank_order(tau: np.ndarray, row_id: np.ndarray) -> np.ndarray:
    """tau'ya göre azalan; eşitlik satır kimliğine göre artan."""
    return np.lexsort((row_id, -tau))


def qini(order, y, t, w) -> tuple[float, np.ndarray]:
    """Qini alanı (N ile bölünmüş, yamuk kuralı, 100 nokta) ve Q(phi_k) eğrisi, k=1..100."""
    yo, to, wo = y[order], t[order], w[order]
    cw = np.cumsum(wo)
    n = cw[-1]
    nt, nc = np.cumsum(wo * to), np.cumsum(wo * (1 - to))
    rt, rc = np.cumsum(wo * to * yo), np.cumsum(wo * (1 - to) * yo)
    phi = np.arange(1, N_POINTS + 1) / N_POINTS
    pos = np.minimum(np.searchsorted(cw, phi * n - 1e-9, side="left"), len(cw) - 1)
    ntk, nck, rtk, rck = nt[pos], nc[pos], rt[pos], rc[pos]
    ratio = np.divide(ntk, nck, out=np.zeros_like(ntk), where=nck > 0)
    q = rtk - rck * ratio
    d = np.concatenate([[0.0], q - phi * q[-1]])
    area = float(np.sum((d[:-1] + d[1:]) / 2) / N_POINTS / n)
    return area, q


def decile_of(order: np.ndarray, n_groups: int = 10) -> np.ndarray:
    """Satır başına desil (0 = en yüksek tau), ham test kümesinde sabitlenir."""
    g = np.empty(len(order), dtype=np.int64)
    g[order] = np.arange(len(order)) * n_groups // len(order)
    return g


def decile_table(tau, y, t, w, dec, n_groups: int = 10) -> dict[str, np.ndarray]:
    size = np.bincount(dec, weights=w, minlength=n_groups)
    tau_m = np.bincount(dec, weights=w * tau, minlength=n_groups) / size
    wt, wc = w * t, w * (1 - t)
    yt = np.bincount(dec, weights=wt * y, minlength=n_groups) / np.bincount(
        dec, weights=wt, minlength=n_groups
    )
    yc = np.bincount(dec, weights=wc * y, minlength=n_groups) / np.bincount(
        dec, weights=wc, minlength=n_groups
    )
    obs = yt - yc
    return {"boyut": size, "tau_hat": tau_m, "tau_obs": obs, "fark": tau_m - obs}


def calibration_slope(tab: dict[str, np.ndarray]) -> float:
    """tau_obs_d = a + b * tau_hat_d, |S_d| ağırlıklı en küçük kareler; b döner."""
    x, y, w = tab["tau_hat"], tab["tau_obs"], tab["boyut"]
    xm, ym = np.average(x, weights=w), np.average(y, weights=w)
    return float(np.sum(w * (x - xm) * (y - ym)) / np.sum(w * (x - xm) ** 2))


def overall_gap(tau, y, t, w) -> float:
    """Ortalama tahmin - gözlenen genel fark."""
    obs = np.average(y, weights=w * t) - np.average(y, weights=w * (1 - t))
    return float(np.average(tau, weights=w) - obs)


def policy_value(pi, y, t, w, p: float, m: float, c: float) -> float:
    """IPW politika değeri (müşteri başına): ağırlık * (m Y - c pi), bilinen p ile."""
    ipw = pi * t / p + (1 - pi) * (1 - t) / (1 - p)
    return float(np.sum(w * ipw * (m * y - c * pi)) / np.sum(w))


def bootstrap_weights(t: np.ndarray, b: int, seed: int = SEED):
    """Tabakalı bootstrap: tedavi ve kontrol kendi içinde yeniden örneklenir; çokluk ağırlığı."""
    rng = np.random.default_rng(seed)
    it, ic = np.flatnonzero(t == 1), np.flatnonzero(t == 0)
    for _ in range(b):
        s = np.concatenate([rng.choice(it, len(it)), rng.choice(ic, len(ic))])
        yield np.bincount(s, minlength=len(t)).astype(float)


def ci(values) -> tuple[float, float]:
    lo, hi = np.percentile(np.asarray(values), [2.5, 97.5])
    return float(lo), float(hi)
