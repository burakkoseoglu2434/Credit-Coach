from __future__ import annotations


def dynamic_alpha(msi: float, base_alpha: float = 0.05, high_stress_alpha: float = 0.01, threshold: float = 0.7) -> float:
    return float(high_stress_alpha if msi > threshold else base_alpha)


def shift_threshold(base_tau: float, msi: float, shift_per_msi_unit: float = -0.02) -> float:
    shifted = base_tau + (shift_per_msi_unit * msi)
    return float(max(0.01, min(0.99, shifted)))
