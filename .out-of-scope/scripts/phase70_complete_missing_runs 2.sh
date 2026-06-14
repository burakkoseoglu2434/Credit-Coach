#!/usr/bin/env bash
set -euo pipefail

# Phase 70.0 — Complete missing audit runs (deterministic, no manifests)
#
# - Skips runs that are already COMPLETE (have cohort_metrics.json + customer_level_analysis.csv).
# - Fails fast if a required run dir exists but is INCOMPLETE (prevents reusing partial/invalid outputs).
# - Never passes --customer_manifest_csv.
# - Does not change model/threshold/planner logic; only runs existing CLIs.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CC_DIR="${REPO_ROOT}/credit-coach"

AUDIT_ROOT_REL_DEFAULT="artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST"
AUDIT_ROOT_REL="${1:-${AUDIT_ROOT_REL_DEFAULT}}"

SMALL_CONFIG_REL="configs/default.yaml"
LARGE_CONFIG_REL="configs/lendingclub_full.yaml"

MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/credit_coach_mplconfig}"

die() { echo "[ERROR] $*" 1>&2; exit 1; }
info() { echo "[INFO] $*"; }

run_complete() {
  local dir="$1"
  [[ -f "${dir}/cohort_metrics.json" && -f "${dir}/customer_level_analysis.csv" ]]
}

ensure_dir_ok() {
  local dir="$1"
  if [[ -L "${dir}" ]]; then
    die "Run dir is a symlink (not allowed): ${dir}"
  fi
  if [[ -e "${dir}" && ! -d "${dir}" ]]; then
    die "Run path exists but is not a directory: ${dir}"
  fi
  if [[ -d "${dir}" && ! $(run_complete "${dir}" && echo ok) ]]; then
    # Directory exists but isn't complete; abort to avoid reusing partial outputs.
    die "Run dir exists but is incomplete (delete/move it, then retry): ${dir}"
  fi
  mkdir -p "${dir}"
}

verify_run() {
  local dir="$1"
  python - <<PY
import json
from pathlib import Path
p = Path("${dir}") / "cohort_metrics.json"
d = json.loads(p.read_text(encoding="utf-8"))
sm = d.get("sampling", {})
sample_size = sm.get("sample_size", sm.get("realized_sample_n"))
manifest_mode = bool(sm.get("manifest_mode", False))
unique_denied_available = sm.get("unique_denied_available")
print(f"sample_size {sample_size}")
print(f"manifest_mode {manifest_mode}")
print(f"unique_denied_available {unique_denied_available}")
if manifest_mode:
    raise SystemExit("manifest_mode must be false for Phase 70 audit runs.")
PY
}

maybe_prepare_data() {
  local cfg_rel="$1"
  local processed_rel="$2"
  local splits_rel="$3"
  if [[ -f "${CC_DIR}/${processed_rel}/train.parquet" && -f "${CC_DIR}/${processed_rel}/test.parquet" && -f "${CC_DIR}/${splits_rel}/split_summary.json" ]]; then
    info "prepare_data already present for ${cfg_rel} (${processed_rel}, ${splits_rel})"
    return 0
  fi
  info "Running prepare_data for ${cfg_rel}"
  (cd "${CC_DIR}" && PYTHONPATH=src python -m credit_coach.cli.run_prepare_data --config "${cfg_rel}")
}

run_eval() {
  local cfg_rel="$1"
  local n="$2"
  local seed="$3"
  local out_rel="$4"
  local out_dir="${CC_DIR}/${out_rel}"
  ensure_dir_ok "${out_dir}"
  if run_complete "${out_dir}"; then
    info "Skip (already complete): ${out_rel}"
    verify_run "${out_dir}"
    return 0
  fi
  info "Run: ${out_rel} (n=${n}, seed=${seed})"
  (cd "${CC_DIR}" && MPLCONFIGDIR="${MPLCONFIGDIR}" PYTHONPATH=src python -m credit_coach.cli.run_v24_cohort_evaluation \
    --base_config "${cfg_rel}" \
    --dataset_scope full_processed \
    --n_customers "${n}" \
    --sample_seed "${seed}" \
    --output_dir "${out_rel}")
  verify_run "${out_dir}"
}

main() {
  info "Repo root: ${REPO_ROOT}"
  info "Audit root (relative to credit-coach): ${AUDIT_ROOT_REL}"

  # Ensure processed data roots exist (non-destructive: only runs if missing).
  maybe_prepare_data "${SMALL_CONFIG_REL}" "data/processed" "data/splits"
  maybe_prepare_data "${LARGE_CONFIG_REL}" "data/processed_lendingclub_full" "data/splits_lendingclub_full"

  # Required runs
  run_eval "${SMALL_CONFIG_REL}" 300 42 "${AUDIT_ROOT_REL}/S1_small_n300_seed42"
  run_eval "${SMALL_CONFIG_REL}" 300 43 "${AUDIT_ROOT_REL}/S2_small_n300_seed43"

  run_eval "${LARGE_CONFIG_REL}" 300 42 "${AUDIT_ROOT_REL}/W1a_large_n300_seed42"
  run_eval "${LARGE_CONFIG_REL}" 300 43 "${AUDIT_ROOT_REL}/W1b_large_n300_seed43"

  run_eval "${LARGE_CONFIG_REL}" 3000 42 "${AUDIT_ROOT_REL}/W2a_large_n3000_seed42"
  run_eval "${LARGE_CONFIG_REL}" 3000 43 "${AUDIT_ROOT_REL}/W2b_large_n3000_seed43"

  run_eval "${LARGE_CONFIG_REL}" 20000 42 "${AUDIT_ROOT_REL}/W3a_large_n20000_seed42"

  # Optional replicate (only if you want it)
  if [[ "${PHASE70_RUN_W3B:-0}" == "1" ]]; then
    run_eval "${LARGE_CONFIG_REL}" 20000 43 "${AUDIT_ROOT_REL}/W3b_large_n20000_seed43"
  else
    info "Skip optional W3b (set PHASE70_RUN_W3B=1 to enable)."
  fi

  info "Running Phase 70 summarizer"
  (cd "${CC_DIR}" && MPLCONFIGDIR="${MPLCONFIGDIR}" PYTHONPATH=src python -m credit_coach.cli.run_phase70_diagnostic_summarize \
    --audit_root "${AUDIT_ROOT_REL}" \
    --small_config "${SMALL_CONFIG_REL}" \
    --large_config "${LARGE_CONFIG_REL}")

  info "Done. Outputs under: ${CC_DIR}/${AUDIT_ROOT_REL}"
}

main "$@"

