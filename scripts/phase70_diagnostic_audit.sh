#!/usr/bin/env bash
# ============================================================
# Phase 70.0 — Large-Data Diagnostic Audit
# Deterministic, measurement-only, no logic changes
# ============================================================

set -euo pipefail

DATE_TAG="${DATE_TAG:-$(date +%Y%m%d)}"
AUDIT_ROOT="credit-coach/artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_${DATE_TAG}"

SMALL_CONFIG="credit-coach/configs/default.yaml"
LARGE_CONFIG="credit-coach/configs/lendingclub_full.yaml"

mkdir -p "${AUDIT_ROOT}"

echo "[INFO] Audit root: ${AUDIT_ROOT}"

PY_BIN="${PY_BIN:-python}"
if [[ -x "credit-coach/.venv/bin/python" ]]; then
  PY_BIN="credit-coach/.venv/bin/python"
fi

fail() {
  echo "[ERROR] $*" >&2
  exit 1
}

assert_output_dir_is_fresh() {
  local out_dir="$1"
  if [[ -L "$out_dir" ]]; then
    fail "Output dir is a symlink (refuse to write): $out_dir"
  fi
  if [[ -e "$out_dir" ]]; then
    fail "Output dir already exists (refuse to overwrite): $out_dir"
  fi
}

assert_no_manifest_and_min_sample() {
  local out_dir="$1"
  local min_sample="$2"
  local metrics_path="$out_dir/cohort_metrics.json"
  [[ -f "$metrics_path" ]] || fail "Missing cohort_metrics.json: $metrics_path"
  PYTHONPATH=src "${PY_BIN}" -c "
import json
from pathlib import Path
p=Path('$metrics_path')
d=json.loads(p.read_text(encoding='utf-8'))
s=d.get('sampling',{}) or {}
e=d.get('evaluation',{}) or {}
sample_size=int(e.get('sample_size') or s.get('realized_sample_n') or 0)
manifest=bool(s.get('manifest_mode', False))
unique_denied=int(s.get('unique_denied_available') or 0)
print('[VERIFY] sample_size=', sample_size, 'manifest_mode=', manifest, 'unique_denied_available=', unique_denied)
assert manifest is False, f'manifest_mode must be false, got {manifest} (manifest_path={s.get(\"manifest_path\")})'
assert sample_size >= int('$min_sample'), f'sample_size too small: {sample_size} < {int('$min_sample')}'
"
}

# ------------------------------------------------------------
# 0) Optional: full dataset prep (large config only)
# Non-destructive processed roots must already be encoded in
# lendingclub_full.yaml:
#   data/processed_lendingclub_full/
#   data/splits_lendingclub_full/
# ------------------------------------------------------------
(
  cd credit-coach
  PYTHONPATH=src "${PY_BIN}" -m credit_coach.cli.run_prepare_data \
    --config configs/lendingclub_full.yaml
)

# ------------------------------------------------------------
# 1) Small baseline reruns (like-for-like anchor)
# ------------------------------------------------------------
(
  cd credit-coach
  assert_output_dir_is_fresh "../${AUDIT_ROOT}/S1_small_n300_seed42"
  PYTHONPATH=src "${PY_BIN}" -m credit_coach.cli.run_v24_cohort_evaluation \
    --base_config configs/default.yaml \
    --dataset_scope full_processed \
    --n_customers 300 \
    --sample_seed 42 \
    --output_dir "../${AUDIT_ROOT}/S1_small_n300_seed42"
)

(
  cd credit-coach
  assert_output_dir_is_fresh "../${AUDIT_ROOT}/S2_small_n300_seed43"
  PYTHONPATH=src "${PY_BIN}" -m credit_coach.cli.run_v24_cohort_evaluation \
    --base_config configs/default.yaml \
    --dataset_scope full_processed \
    --n_customers 300 \
    --sample_seed 43 \
    --output_dir "../${AUDIT_ROOT}/S2_small_n300_seed43"
)

# ------------------------------------------------------------
# 2) Wave 1 — Large dataset smoke
# ------------------------------------------------------------
(
  cd credit-coach
  assert_output_dir_is_fresh "../${AUDIT_ROOT}/W1a_large_n300_seed42"
  PYTHONPATH=src "${PY_BIN}" -m credit_coach.cli.run_v24_cohort_evaluation \
    --base_config configs/lendingclub_full.yaml \
    --dataset_scope full_processed \
    --n_customers 300 \
    --sample_seed 42 \
    --output_dir "../${AUDIT_ROOT}/W1a_large_n300_seed42"
  assert_no_manifest_and_min_sample "../${AUDIT_ROOT}/W1a_large_n300_seed42" 200
)

(
  cd credit-coach
  assert_output_dir_is_fresh "../${AUDIT_ROOT}/W1b_large_n300_seed43"
  PYTHONPATH=src "${PY_BIN}" -m credit_coach.cli.run_v24_cohort_evaluation \
    --base_config configs/lendingclub_full.yaml \
    --dataset_scope full_processed \
    --n_customers 300 \
    --sample_seed 43 \
    --output_dir "../${AUDIT_ROOT}/W1b_large_n300_seed43"
  assert_no_manifest_and_min_sample "../${AUDIT_ROOT}/W1b_large_n300_seed43" 200
)

# ------------------------------------------------------------
# 3) Wave 2 — Large dataset medium scale
# ------------------------------------------------------------
(
  cd credit-coach
  assert_output_dir_is_fresh "../${AUDIT_ROOT}/W2a_large_n3000_seed42"
  PYTHONPATH=src "${PY_BIN}" -m credit_coach.cli.run_v24_cohort_evaluation \
    --base_config configs/lendingclub_full.yaml \
    --dataset_scope full_processed \
    --n_customers 3000 \
    --sample_seed 42 \
    --output_dir "../${AUDIT_ROOT}/W2a_large_n3000_seed42"
)

(
  cd credit-coach
  assert_output_dir_is_fresh "../${AUDIT_ROOT}/W2b_large_n3000_seed43"
  PYTHONPATH=src "${PY_BIN}" -m credit_coach.cli.run_v24_cohort_evaluation \
    --base_config configs/lendingclub_full.yaml \
    --dataset_scope full_processed \
    --n_customers 3000 \
    --sample_seed 43 \
    --output_dir "../${AUDIT_ROOT}/W2b_large_n3000_seed43"
)

# ------------------------------------------------------------
# 4) Wave 3 — Large dataset stress
# ------------------------------------------------------------
(
  cd credit-coach
  assert_output_dir_is_fresh "../${AUDIT_ROOT}/W3a_large_n20000_seed42"
  PYTHONPATH=src "${PY_BIN}" -m credit_coach.cli.run_v24_cohort_evaluation \
    --base_config configs/lendingclub_full.yaml \
    --dataset_scope full_processed \
    --n_customers 20000 \
    --sample_seed 42 \
    --output_dir "../${AUDIT_ROOT}/W3a_large_n20000_seed42"
)

# Optional second stress replicate if runtime budget permits
(
  cd credit-coach
  assert_output_dir_is_fresh "../${AUDIT_ROOT}/W3b_large_n20000_seed43"
  PYTHONPATH=src "${PY_BIN}" -m credit_coach.cli.run_v24_cohort_evaluation \
    --base_config configs/lendingclub_full.yaml \
    --dataset_scope full_processed \
    --n_customers 20000 \
    --sample_seed 43 \
    --output_dir "../${AUDIT_ROOT}/W3b_large_n20000_seed43"
)

echo "[OK] Cohort evaluation runs completed."

# ------------------------------------------------------------
# 5) Deterministic summarization + reporting
# ------------------------------------------------------------
(
  cd credit-coach
  MPLCONFIGDIR="/tmp/credit_coach_mplconfig" PYTHONPATH=src "${PY_BIN}" -m credit_coach.cli.run_phase70_diagnostic_summarize \
    --audit_root "../${AUDIT_ROOT}" \
    --small_config "../${SMALL_CONFIG}" \
    --large_config "../${LARGE_CONFIG}"
)

echo "[OK] Diagnostic outputs written under: ${AUDIT_ROOT}"
