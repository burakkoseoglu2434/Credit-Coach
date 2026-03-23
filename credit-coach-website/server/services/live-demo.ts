import { execFile } from "node:child_process";
import { promises as fs } from "node:fs";
import os from "node:os";
import path from "node:path";
import { promisify } from "node:util";

import {
  singleCustomerDemoSchema,
  type SingleCustomerDemo,
} from "../../shared/demo-schema.js";

const execFileAsync = promisify(execFile);

const CACHE_TTL_MS = 15 * 60 * 1000;
const DEMO_CUSTOMER_ID = "website_demo_customer";
const DEMO_ROW_INDEX = 114;
const REQUIRED_DECISION_STATUS = "APPROVED";
const PYTHON_BINS = ["python", "python3"];
const DEMO_DB_URL = "sqlite:///./credit_coach_demo_state.db";

const ACTION_DETAILS: Record<string, string> = {
  adjust_requested_loan_amount:
    "Reduce the requested amount to a level that matches current affordability and improves approval readiness.",
  refinance:
    "Pursue refinancing only after the earlier checkpoints are stable enough to support a stronger application.",
  increase_regular_income:
    "Strengthen recurring income through stable and documentable sources before the next review window.",
  verify_income_documentation:
    "Complete income verification so the lender sees a cleaner and more dependable file.",
  reduce_spending:
    "Lower non-essential monthly spending to create short-term affordability and repayment headroom.",
  debt_consolidation:
    "Move high-pressure revolving balances into a more structured path that is easier to sustain.",
  limit_credit_usage:
    "Reduce card usage and avoid adding new balance pressure while the profile is stabilizing.",
  improve_payment_consistency:
    "Maintain consistent on-time payments to rebuild lender confidence over the next checkpoints.",
  credit_limit_adjustment:
    "Use a lender-managed limit adjustment only where it meaningfully improves utilization headroom.",
  settlement_discount:
    "Consider a negotiated settlement only when the institution confirms eligible terms and customer fit.",
  installment_plan:
    "Convert eligible balances into a structured installment path to make repayment behavior more stable.",
};

const FEATURE_ACTIONS: Record<
  string,
  {
    action_key: string;
    action_class: string;
    action_title: string;
  }
> = {
  loan_amnt: {
    action_key: "adjust_requested_loan_amount",
    action_class: "structural",
    action_title: "Adjust requested loan amount",
  },
  int_rate: {
    action_key: "refinance",
    action_class: "structural",
    action_title: "Refinance or restructure debt",
  },
  installment: {
    action_key: "refinance",
    action_class: "structural",
    action_title: "Refinance or restructure debt",
  },
  annual_inc: {
    action_key: "increase_regular_income",
    action_class: "behavioral",
    action_title: "Increase regular income",
  },
  verification_status: {
    action_key: "verify_income_documentation",
    action_class: "structural",
    action_title: "Verify income documentation",
  },
  dti: {
    action_key: "reduce_spending",
    action_class: "behavioral",
    action_title: "Reduce spending pressure",
  },
  revol_bal: {
    action_key: "debt_consolidation",
    action_class: "structural",
    action_title: "Consolidate revolving debt",
  },
  tot_cur_bal: {
    action_key: "debt_consolidation",
    action_class: "structural",
    action_title: "Consolidate revolving debt",
  },
  total_bal_ex_mort: {
    action_key: "debt_consolidation",
    action_class: "structural",
    action_title: "Consolidate revolving debt",
  },
  revol_util: {
    action_key: "limit_credit_usage",
    action_class: "behavioral",
    action_title: "Limit credit usage",
  },
  fico_range_low: {
    action_key: "improve_payment_consistency",
    action_class: "behavioral",
    action_title: "Improve payment consistency",
  },
  fico_range_high: {
    action_key: "improve_payment_consistency",
    action_class: "behavioral",
    action_title: "Improve payment consistency",
  },
  last_fico_range_low: {
    action_key: "improve_payment_consistency",
    action_class: "behavioral",
    action_title: "Improve payment consistency",
  },
  last_fico_range_high: {
    action_key: "improve_payment_consistency",
    action_class: "behavioral",
    action_title: "Improve payment consistency",
  },
  total_rev_hi_lim: {
    action_key: "credit_limit_adjustment",
    action_class: "institutional",
    action_title: "Request or negotiate credit limit adjustment",
  },
  total_bc_limit: {
    action_key: "credit_limit_adjustment",
    action_class: "institutional",
    action_title: "Request or negotiate credit limit adjustment",
  },
  tot_hi_cred_lim: {
    action_key: "credit_limit_adjustment",
    action_class: "institutional",
    action_title: "Request or negotiate credit limit adjustment",
  },
  acc_now_delinq: {
    action_key: "installment_plan",
    action_class: "institutional",
    action_title: "Enter an installment plan",
  },
  delinq_amnt: {
    action_key: "installment_plan",
    action_class: "institutional",
    action_title: "Enter an installment plan",
  },
  collections_12_mths_ex_med: {
    action_key: "installment_plan",
    action_class: "institutional",
    action_title: "Enter an installment plan",
  },
  tot_coll_amt: {
    action_key: "settlement_discount",
    action_class: "institutional",
    action_title: "Negotiate settlement discount",
  },
};

type RawPlanRow = Record<string, unknown>;
type RawRoadmapStep = {
  step_id?: unknown;
  action_key?: unknown;
  action_class?: unknown;
  action_title?: unknown;
  action_group_id?: unknown;
  business_view?: unknown;
  technical_view?: unknown;
  primary_numeric_target?: unknown;
  offer_contract?: unknown;
  time_months?: unknown;
  estimated_cost_usd?: unknown;
  action_execution_probability?: unknown;
  action_group_execution_probability?: unknown;
  approval_dependent_probability?: unknown;
  difficulty_score?: unknown;
  difficulty_label?: unknown;
  offer_type?: unknown;
  narrative?: unknown;
};

type RawRoadmapPhase = {
  phase_id?: unknown;
  phase_title?: unknown;
  target_window_weeks?: unknown;
  target_pd?: unknown;
  steps?: RawRoadmapStep[];
};

type RawCheckpoint = {
  checkpoint_id?: unknown;
  week?: unknown;
  checkpoint_label?: unknown;
  predicted_pd?: unknown;
  gate_pass_estimate?: unknown;
  narrative?: unknown;
};

type RawRoadmapNarrative = SingleCustomerDemo["narrative"];

type RawRoadmap = {
  customer_id?: unknown;
  base_pd?: unknown;
  tau?: unknown;
  best_plan_id?: unknown;
  best_status?: unknown;
  trajectory_status?: unknown;
  summary?: Record<string, unknown>;
  contract_health?: Record<string, unknown>;
  phases?: RawRoadmapPhase[];
  checkpoints?: RawCheckpoint[];
  narrative?: RawRoadmapNarrative;
};

type RawMetrics = Record<string, unknown>;

type RunArtifacts = {
  runId: string;
  roadmapPath: string;
  plansPath: string;
  metricsPath: string;
  generatedAt: string;
};

type CachedDemo = {
  data: SingleCustomerDemo;
  expiresAt: number;
};

type NormalizedRoadmapStep = SingleCustomerDemo["phases"][number]["steps"][number];
type NormalizedBusinessView = NonNullable<NormalizedRoadmapStep["business_view"]>;
type NormalizedTechnicalView = NonNullable<NormalizedRoadmapStep["technical_view"]>;
type NormalizedPrimaryNumericTarget = NonNullable<NormalizedRoadmapStep["primary_numeric_target"]>;
type NormalizedOfferContract = NonNullable<NormalizedRoadmapStep["offer_contract"]>;
type NormalizedOfferTerms = NonNullable<NormalizedOfferContract["offer_terms"]>;

let cachedDemo: CachedDemo | null = null;
let inFlightDemo: Promise<SingleCustomerDemo> | null = null;

function websiteRootDir() {
  const cwd = process.cwd();
  return cwd.endsWith("credit-coach-website")
    ? cwd
    : path.resolve(cwd, "credit-coach-website");
}

function repoRootDir() {
  return path.resolve(websiteRootDir(), "..");
}

function creditCoachRootDir() {
  return path.resolve(repoRootDir(), "credit-coach");
}

function demoProcessedDir() {
  return path.resolve(creditCoachRootDir(), "data", "website_demo", "processed");
}

function demoRegistryDir() {
  return path.resolve(creditCoachRootDir(), "artifacts", "models_website_demo");
}

function runsRootDir() {
  return path.resolve(creditCoachRootDir(), "artifacts", "runs");
}

async function fileExists(filePath: string) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

function toNumber(value: unknown, defaultValue = 0) {
  return typeof value === "number" && Number.isFinite(value) ? value : Number(value ?? defaultValue) || defaultValue;
}

function toStringValue(value: unknown, defaultValue = "") {
  return typeof value === "string" ? value : defaultValue;
}

function toBoolean(value: unknown) {
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    return value !== 0;
  }
  if (typeof value === "string") {
    return value === "1" || value.toLowerCase() === "true";
  }
  return false;
}

function normalizeExpectedReadiness(
  value: unknown,
): SingleCustomerDemo["summary"]["expected_readiness"] | undefined {
  const normalized = toStringValue(value).trim().toLowerCase();
  if (
    normalized === "now" ||
    normalized === "week_4" ||
    normalized === "week_12" ||
    normalized === "week_24" ||
    normalized === "not_ready" ||
    normalized === "unknown_review"
  ) {
    return normalized;
  }
  return undefined;
}

function normalizeDecisionStatus(
  value: unknown,
): SingleCustomerDemo["summary"]["decision_status"] | undefined {
  const normalized = toStringValue(value).trim().toUpperCase();
  if (normalized === "APPROVED" || normalized === "CONDITIONAL" || normalized === "REJECTED") {
    return normalized as SingleCustomerDemo["summary"]["decision_status"];
  }
  return undefined;
}

function normalizeConditionalType(
  value: unknown,
): SingleCustomerDemo["summary"]["conditional_type"] | undefined {
  const normalized = toStringValue(value).trim().toUpperCase();
  if (
    normalized === "DATA_ISSUE" ||
    normalized === "OFFER_GATED" ||
    normalized === "TIME_GATED" ||
    normalized === "EXECUTION_GATED"
  ) {
    return normalized as SingleCustomerDemo["summary"]["conditional_type"];
  }
  return undefined;
}

function normalizeCreditReadinessStage(
  value: unknown,
  fallback: SingleCustomerDemo["summary"]["credit_readiness_stage"],
): SingleCustomerDemo["summary"]["credit_readiness_stage"] {
  const normalized = toStringValue(value).trim().toLowerCase();
  if (
    normalized === "now" ||
    normalized === "week_4" ||
    normalized === "week_12" ||
    normalized === "week_24" ||
    normalized === "not_ready_yet"
  ) {
    return normalized as SingleCustomerDemo["summary"]["credit_readiness_stage"];
  }
  if (normalized === "not_ready" || normalized === "unknown_review") {
    return "not_ready_yet";
  }
  return fallback;
}

function toRecord(value: unknown) {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;
}

function toNullableNumber(value: unknown) {
  if (value === null) {
    return null;
  }
  return typeof value === "number" && Number.isFinite(value)
    ? value
    : undefined;
}

function toBusinessView(value: unknown): NormalizedBusinessView | undefined {
  const record = toRecord(value);
  if (!record) {
    return undefined;
  }
  return {
    action_key: toStringValue(record.action_key) || undefined,
    action_family: toStringValue(record.action_family) || undefined,
    action_class: toStringValue(record.action_class) || undefined,
    action_title: toStringValue(record.action_title) || undefined,
    action_description: toStringValue(record.action_description) || undefined,
    action_group_id: toStringValue(record.action_group_id) || undefined,
  };
}

function toTechnicalView(value: unknown): NormalizedTechnicalView | undefined {
  const record = toRecord(value);
  const featureName = toStringValue(record?.feature_name);
  if (!record || !featureName) {
    return undefined;
  }
  return {
    feature_name: featureName,
    current_value: toNullableNumber(record.current_value),
    target_value: toNullableNumber(record.target_value),
    delta: toNullableNumber(record.delta),
    time_months: toNullableNumber(record.time_months),
    phase_id: toStringValue(record.phase_id) || undefined,
    week_start: toNullableNumber(record.week_start),
    week_end: toNullableNumber(record.week_end),
    checkpoint_metric: toStringValue(record.checkpoint_metric) || undefined,
  };
}

function toPrimaryNumericTarget(value: unknown): NormalizedPrimaryNumericTarget | undefined {
  const record = toRecord(value);
  const metricKey = toStringValue(record?.metric_key);
  const unit = toStringValue(record?.unit);
  const targetValue =
    typeof record?.target_value === "number" && Number.isFinite(record.target_value)
      ? record.target_value
      : undefined;
  const deltaValue =
    typeof record?.delta_value === "number" && Number.isFinite(record.delta_value)
      ? record.delta_value
      : undefined;
  const dueMonth =
    typeof record?.due_month === "number" && Number.isFinite(record.due_month)
      ? record.due_month
      : undefined;
  const direction = toStringValue(record?.direction);
  if (
    !record ||
    !metricKey ||
    !["currency", "percentage_points", "ratio", "score_points", "months", "boolean_state", "count"].includes(unit) ||
    targetValue === undefined ||
    deltaValue === undefined ||
    dueMonth === undefined ||
    !["decrease", "increase"].includes(direction)
  ) {
    return undefined;
  }
  return {
    metric_key: metricKey,
    unit: unit as NormalizedPrimaryNumericTarget["unit"],
    current_value: toNullableNumber(record.current_value),
    target_value: targetValue,
    delta_value: deltaValue,
    due_month: dueMonth,
    direction: direction as NormalizedPrimaryNumericTarget["direction"],
    generation_notes: Array.isArray(record.generation_notes)
      ? record.generation_notes.filter((note): note is string => typeof note === "string")
      : undefined,
    raw_generation_basis: toRecord(record.raw_generation_basis),
  };
}

function toOfferTerms(value: unknown): NormalizedOfferTerms | undefined {
  const record = toRecord(value);
  if (!record) {
    return undefined;
  }
  return {
    payment_delta_monthly: toNullableNumber(record.payment_delta_monthly),
    discount_amount: toNullableNumber(record.discount_amount),
    discount_pct: toNullableNumber(record.discount_pct),
    term_extension_months: toNullableNumber(record.term_extension_months),
    interest_rate_delta: toNullableNumber(record.interest_rate_delta),
    grace_period_weeks: toNullableNumber(record.grace_period_weeks),
    extensions: toRecord(record.extensions),
  };
}

function toOfferContract(value: unknown): NormalizedOfferContract | undefined {
  const record = toRecord(value);
  if (!record) {
    return undefined;
  }
  const approvalState = toStringValue(record.institutional_approval_state);
  return {
    offer_type: toStringValue(record.offer_type) || undefined,
    offer_family: toStringValue(record.offer_family) || undefined,
    offer_terms: toOfferTerms(record.offer_terms),
    offer_terms_complete:
      typeof record.offer_terms_complete === "boolean" ? record.offer_terms_complete : undefined,
    requires_acceptance:
      typeof record.requires_acceptance === "boolean" ? record.requires_acceptance : undefined,
    requires_institutional_approval:
      typeof record.requires_institutional_approval === "boolean"
        ? record.requires_institutional_approval
        : undefined,
    institutional_approval_state: ["not_required", "approved", "pending", "unknown"].includes(approvalState)
      ? (approvalState as NormalizedOfferContract["institutional_approval_state"])
      : undefined,
    offer_policy_arm: toStringValue(record.offer_policy_arm) || undefined,
    offer_scoring_profile: toStringValue(record.offer_scoring_profile) || undefined,
    term_generation_rule: toStringValue(record.term_generation_rule) || undefined,
  };
}

async function readJsonFile<T>(filePath: string): Promise<T> {
  return JSON.parse(await fs.readFile(filePath, "utf-8")) as T;
}

async function ensurePythonCacheDirs() {
  const mplConfigDir = path.resolve(websiteRootDir(), ".cache", "matplotlib");
  await fs.mkdir(mplConfigDir, { recursive: true });
  return mplConfigDir;
}

async function runPythonCommand(args: string[], label: string) {
  const mplConfigDir = await ensurePythonCacheDirs();
  let lastError: Error | null = null;

  for (const pythonBin of PYTHON_BINS) {
    try {
      await execFileAsync(pythonBin, args, {
        cwd: creditCoachRootDir(),
        env: {
          ...process.env,
          DB_URL: DEMO_DB_URL,
          MPLCONFIGDIR: mplConfigDir,
          PYTHONUNBUFFERED: "1",
          PYTHONIOENCODING: "utf-8",
          TMPDIR: os.tmpdir(),
        },
        maxBuffer: 10 * 1024 * 1024,
      });
      return;
    } catch (error) {
      const execError = error as NodeJS.ErrnoException & {
        stdout?: string;
        stderr?: string;
      };
      if (execError.code === "ENOENT") {
        lastError = execError;
        continue;
      }

      const detail = [execError.stdout, execError.stderr].filter(Boolean).join("\n").trim();
      throw new Error(`${label} failed.\n${detail || execError.message}`);
    }
  }

  throw new Error(lastError?.message || `${label} failed: python executable not found.`);
}

async function ensureWebsiteDemoAssets() {
  await runPythonCommand(
    ["-c", "from credit_coach.storage.db import init_db; init_db()"],
    "Website demo database init",
  );

  const trainPath = path.resolve(demoProcessedDir(), "train.parquet");
  const testPath = path.resolve(demoProcessedDir(), "test.parquet");
  if (!(await fileExists(trainPath)) || !(await fileExists(testPath))) {
    await runPythonCommand(
      ["-m", "credit_coach.cli.run_prepare_data", "--config", "configs/website_demo.yaml"],
      "Website demo data preparation",
    );
  }

  const latestManifestPath = path.resolve(demoRegistryDir(), "latest.json");
  if (!(await fileExists(latestManifestPath))) {
    await runPythonCommand(
      [
        "-m",
        "credit_coach.cli.run_train",
        "--base_config",
        "configs/website_demo.yaml",
        "--config",
        "configs/model_website_demo.yaml",
      ],
      "Website demo model training",
    );
  }
}

async function findLatestRunArtifacts(afterTimestampMs = 0): Promise<RunArtifacts> {
  const entries = await fs.readdir(runsRootDir(), { withFileTypes: true });
  const candidates: Array<RunArtifacts & { mtimeMs: number }> = [];

  for (const entry of entries) {
    if (!entry.isDirectory()) {
      continue;
    }

    const runId = entry.name;
    const runDir = path.resolve(runsRootDir(), runId);
    const roadmapPath = path.resolve(runDir, "tables", "customer_roadmap.json");
    const plansPath = path.resolve(runDir, "tables", "plans.json");
    const metricsPath = path.resolve(runDir, "metrics.json");

    if (!(await fileExists(roadmapPath)) || !(await fileExists(plansPath)) || !(await fileExists(metricsPath))) {
      continue;
    }

    const roadmapStat = await fs.stat(roadmapPath);
    candidates.push({
      runId,
      roadmapPath,
      plansPath,
      metricsPath,
      generatedAt: roadmapStat.mtime.toISOString(),
      mtimeMs: roadmapStat.mtimeMs,
    });
  }

  candidates.sort((left, right) => right.mtimeMs - left.mtimeMs);
  const selected =
    candidates.find((candidate) => candidate.mtimeMs >= afterTimestampMs) ?? candidates[0];

  if (!selected) {
    throw new Error("No recourse run artifacts found for the website demo.");
  }

  return selected;
}

function getCheckpoint(rawRoadmap: RawRoadmap, week: number) {
  return (rawRoadmap.checkpoints ?? []).find((checkpoint) => toNumber(checkpoint.week) === week);
}

function fallbackCheckpointLabel(week: number) {
  if (week === 4) {
    return "Early stabilization";
  }
  if (week === 12) {
    return "Approval readiness";
  }
  if (week === 24) {
    return "Durable optimization";
  }
  return `Week ${week} review`;
}

function phaseTargetPd(rawRoadmap: RawRoadmap, phaseId: string, phaseTargetPdValue: unknown) {
  const explicitTargetPd = toNumber(phaseTargetPdValue, Number.NaN);
  if (!Number.isNaN(explicitTargetPd) && explicitTargetPd > 0) {
    return explicitTargetPd;
  }

  if (phaseId === "phase_1_stabilize") {
    return toNumber(getCheckpoint(rawRoadmap, 4)?.predicted_pd, toNumber(rawRoadmap.base_pd));
  }
  if (phaseId === "phase_2_build") {
    return toNumber(getCheckpoint(rawRoadmap, 12)?.predicted_pd, toNumber(rawRoadmap.base_pd));
  }

  return toNumber(getCheckpoint(rawRoadmap, 24)?.predicted_pd, toNumber(rawRoadmap.base_pd));
}

function isApprovalReady(checkpoint: RawCheckpoint | undefined, tau: number) {
  if (!checkpoint) {
    return false;
  }

  return toNumber(checkpoint.predicted_pd, 1) <= tau && toBoolean(checkpoint.gate_pass_estimate);
}

function computeReadinessStage(rawRoadmap: RawRoadmap) {
  const tau = toNumber(rawRoadmap.tau, 0.35);
  const approvalReadyNow = toNumber(rawRoadmap.base_pd, 1) <= tau;
  const approvalReady4w = isApprovalReady(getCheckpoint(rawRoadmap, 4), tau);
  const approvalReady12w = isApprovalReady(getCheckpoint(rawRoadmap, 12), tau);
  const approvalReady24w = isApprovalReady(getCheckpoint(rawRoadmap, 24), tau);

  let creditReadinessStage: SingleCustomerDemo["summary"]["credit_readiness_stage"] = "not_ready_yet";
  if (approvalReadyNow) {
    creditReadinessStage = "now";
  } else if (approvalReady4w) {
    creditReadinessStage = "week_4";
  } else if (approvalReady12w) {
    creditReadinessStage = "week_12";
  } else if (approvalReady24w) {
    creditReadinessStage = "week_24";
  }

  return {
    approvalReadyNow,
    approvalReady4w,
    approvalReady12w,
    approvalReady24w,
    creditReadinessStage,
  };
}

function stepDetailFor(actionKey: string) {
  return ACTION_DETAILS[actionKey] ?? "Follow this step within the suggested window to improve credit readiness safely.";
}

function fallbackStepExecutionProbability(
  actionClass: string,
  timeMonths: number,
  estimatedCostUsd: number,
  offerType: string,
) {
  let probability = 0.62;
  if (actionClass === "behavioral") {
    probability = 0.72;
  } else if (actionClass === "structural") {
    probability = 0.58;
  } else if (actionClass === "institutional") {
    probability = 0.49;
  }

  if (timeMonths >= 3) {
    probability -= 0.04;
  }
  if (timeMonths >= 6) {
    probability -= 0.03;
  }
  if (estimatedCostUsd >= 50) {
    probability -= 0.04;
  }
  if (estimatedCostUsd >= 100) {
    probability -= 0.04;
  }
  if (offerType) {
    probability -= 0.05;
  }

  return Math.max(0.25, Math.min(0.9, probability));
}

function inferActionMeta(step: RawRoadmapStep & { feature_name?: unknown }) {
  const featureName = toStringValue(step.feature_name);
  const fallback = FEATURE_ACTIONS[featureName];
  const actionKey = toStringValue(step.action_key, fallback?.action_key ?? "improve_payment_consistency");
  const actionClass = toStringValue(step.action_class, fallback?.action_class ?? "behavioral");
  const actionTitle = toStringValue(
    step.action_title,
    fallback?.action_title ?? "Improve repayment readiness",
  );

  return {
    actionKey,
    actionClass,
    actionTitle,
  };
}

function normalizeSingleCustomerDemo(
  rawRoadmap: RawRoadmap,
  rawPlans: RawPlanRow[],
  rawMetrics: RawMetrics,
  runArtifacts: RunArtifacts,
): SingleCustomerDemo {
  const summary = (rawRoadmap.summary ?? {}) as Record<string, unknown>;
  const checkpoint4w = getCheckpoint(rawRoadmap, 4);
  const checkpoint12w = getCheckpoint(rawRoadmap, 12);
  const checkpoint24w = getCheckpoint(rawRoadmap, 24);
  const bestPlanId = toStringValue(rawRoadmap.best_plan_id);
  const bestPlan =
    rawPlans.find((plan) => toStringValue(plan.plan_id) === bestPlanId) ??
    rawPlans[0] ??
    {};
  const readiness = computeReadinessStage(rawRoadmap);
  const stepNarrativeMap = new Map(
    (rawRoadmap.narrative?.steps ?? []).map((entry) => [entry.step_id, entry] as const),
  );
  const checkpointNarrativeMap = new Map(
    (rawRoadmap.narrative?.checkpoints ?? []).map((entry) => [entry.checkpoint_id, entry] as const),
  );

  const phases = (rawRoadmap.phases ?? []).map((phase) => ({
    phase_id: toStringValue(phase.phase_id),
    phase_title: toStringValue(phase.phase_title),
    target_window_weeks: toStringValue(phase.target_window_weeks),
    target_pd: phaseTargetPd(rawRoadmap, toStringValue(phase.phase_id), phase.target_pd),
    steps: (phase.steps ?? []).map((step) => {
      const actionMeta = inferActionMeta(step);
      const stepId = toStringValue(
        step.step_id,
        `${toStringValue(phase.phase_id, "phase")}:${actionMeta.actionKey}:${toNumber(step.time_months, 1)}`,
      );
      const timeMonths = toNumber(step.time_months, 1);
      const estimatedCostUsd = toNumber(step.estimated_cost_usd);
      const offerType = toStringValue(step.offer_type);
      const difficultyScore =
        typeof step.difficulty_score === "number" && Number.isFinite(step.difficulty_score)
          ? step.difficulty_score
          : undefined;
      const fallbackProbability = fallbackStepExecutionProbability(
        actionMeta.actionClass,
        timeMonths,
        estimatedCostUsd,
        offerType,
      );
      return {
        step_id: stepId,
        action_key: actionMeta.actionKey,
        action_class: actionMeta.actionClass,
        action_title: actionMeta.actionTitle,
        action_group_id: toStringValue(step.action_group_id),
        detail: stepDetailFor(actionMeta.actionKey),
        time_months: timeMonths,
        estimated_cost_usd: estimatedCostUsd,
        plan_execution_probability: toNumber(
          step.action_execution_probability ?? step.action_group_execution_probability,
          fallbackProbability,
        ),
        action_execution_probability: toNumber(step.action_execution_probability, fallbackProbability),
        action_group_execution_probability: toNumber(
          step.action_group_execution_probability,
          fallbackProbability,
        ),
        approval_dependent_probability: toNumber(step.approval_dependent_probability, 0),
        difficulty_score: difficultyScore,
        difficulty_label: toStringValue(step.difficulty_label),
        business_view: toBusinessView(step.business_view),
        technical_view: toTechnicalView(step.technical_view),
        primary_numeric_target: toPrimaryNumericTarget(step.primary_numeric_target),
        offer_contract: toOfferContract(step.offer_contract),
        offer_type: offerType,
        narrative: stepNarrativeMap.get(stepId),
      };
    }),
  }));
  const allSteps = phases.flatMap((phase) => phase.steps);
  const inferredPlanExecutionProbability =
    allSteps.length > 0
      ? allSteps.reduce((total, step) => total + (step.plan_execution_probability ?? 0), 0) / allSteps.length
      : 0.6;
  const inferredOfferAcceptanceProbability =
    allSteps.some((step) => Boolean(step.offer_type)) ? 0.48 : 0;
  const planExecutionProbability = toNumber(
    summary.plan_execution_probability ?? bestPlan.plan_execution_probability,
    inferredPlanExecutionProbability,
  );
  const offerAcceptanceProbability = toNumber(
    summary.offer_acceptance_probability ?? bestPlan.offer_acceptance_probability,
    inferredOfferAcceptanceProbability,
  );
  const combinedPlanRealizationProbability = toNumber(
    summary.combined_plan_realization_probability ?? bestPlan.combined_plan_realization_probability,
    offerAcceptanceProbability > 0
      ? planExecutionProbability * offerAcceptanceProbability
      : planExecutionProbability,
  );
  const approvalReadyNow =
    summary.approval_ready_now === undefined ? readiness.approvalReadyNow : toBoolean(summary.approval_ready_now);
  const approvalReady4w =
    summary.approval_ready_4w === undefined ? readiness.approvalReady4w : toBoolean(summary.approval_ready_4w);
  const approvalReady12w =
    summary.approval_ready_12w === undefined ? readiness.approvalReady12w : toBoolean(summary.approval_ready_12w);
  const approvalReady24w =
    summary.approval_ready_24w === undefined ? readiness.approvalReady24w : toBoolean(summary.approval_ready_24w);
  const expectedReadiness = normalizeExpectedReadiness(summary.expected_readiness);
  const creditReadinessStage = normalizeCreditReadinessStage(
    expectedReadiness ?? summary.credit_readiness_stage,
    readiness.creditReadinessStage,
  );
  const decisionStatus = normalizeDecisionStatus(summary.decision_status ?? rawMetrics.decision_status) ?? "CONDITIONAL";
  const decisionConfidence =
    typeof summary.decision_confidence === "number" || typeof summary.decision_confidence === "string"
      ? toNumber(summary.decision_confidence)
      : undefined;

  const content: SingleCustomerDemo = {
    customer: {
      customer_id: toStringValue(rawRoadmap.customer_id, DEMO_CUSTOMER_ID),
      profile: "declined_recovery_candidate",
      segment: "recovery_candidate",
      risk_band: toStringValue(rawMetrics.risk_band, "mid"),
      income_band: toStringValue(rawMetrics.income_band, "q2"),
    },
    summary: {
      base_pd: toNumber(rawRoadmap.base_pd),
      target_pd_4w: toNumber(checkpoint4w?.predicted_pd, toNumber(rawMetrics.trajectory_pd_4w)),
      target_pd_12w: toNumber(checkpoint12w?.predicted_pd, toNumber(rawMetrics.trajectory_pd_12w)),
      target_pd_24w: toNumber(checkpoint24w?.predicted_pd, toNumber(rawMetrics.trajectory_pd_24w)),
      plan_execution_probability: planExecutionProbability,
      offer_acceptance_probability: offerAcceptanceProbability,
      combined_plan_realization_probability: combinedPlanRealizationProbability,
      trajectory_status: toStringValue(summary.trajectory_status ?? rawRoadmap.trajectory_status, "on_track"),
      decision_status: decisionStatus,
      decision_confidence: decisionConfidence,
      decision_reason_summary: toStringValue(summary.decision_reason_summary),
      expected_readiness: expectedReadiness,
      conditional_type: normalizeConditionalType(summary.conditional_type),
      upgrade_condition: toStringValue(summary.upgrade_condition),
      decision_policy_version: toStringValue(summary.decision_policy_version),
      approval_ready_now: approvalReadyNow,
      approval_ready_4w: approvalReady4w,
      approval_ready_12w: approvalReady12w,
      approval_ready_24w: approvalReady24w,
      credit_readiness_stage: creditReadinessStage,
    },
    phases,
    checkpoints: (rawRoadmap.checkpoints ?? []).map((checkpoint) => ({
      checkpoint_id: toStringValue(
        checkpoint.checkpoint_id,
        `checkpoint_week_${toNumber(checkpoint.week)}`,
      ),
      week: toNumber(checkpoint.week),
      checkpoint_label: toStringValue(
        checkpoint.checkpoint_label,
        fallbackCheckpointLabel(toNumber(checkpoint.week)),
      ),
      predicted_pd: toNumber(checkpoint.predicted_pd),
      gate_pass_estimate: toBoolean(checkpoint.gate_pass_estimate),
      note:
        checkpointNarrativeMap.get(
          toStringValue(checkpoint.checkpoint_id, `checkpoint_week_${toNumber(checkpoint.week)}`),
        )?.expected_state.en ?? "Checkpoint review generated from the live recourse model run.",
      approval_ready: isApprovalReady(checkpoint, toNumber(rawRoadmap.tau, 0.35)),
      narrative: checkpointNarrativeMap.get(
        toStringValue(checkpoint.checkpoint_id, `checkpoint_week_${toNumber(checkpoint.week)}`),
      ),
    })),
    narrative: rawRoadmap.narrative,
    meta: {
      live: true,
      source: "live_python_model",
      run_id: runArtifacts.runId,
      generated_at: runArtifacts.generatedAt,
    },
  };

  return singleCustomerDemoSchema.parse(content);
}

async function buildLiveSingleCustomerDemo() {
  await ensureWebsiteDemoAssets();

  const recourseStartMs = Date.now();
  await runPythonCommand(
    [
      "-m",
      "credit_coach.cli.run_recourse",
      "--customer_id",
      DEMO_CUSTOMER_ID,
      "--row_index",
      String(DEMO_ROW_INDEX),
      "--base_config",
      "configs/website_demo.yaml",
      "--model_config",
      "configs/model_website_demo.yaml",
    ],
    "Website demo recourse run",
  );

  const runArtifacts = await findLatestRunArtifacts(recourseStartMs - 1000);
  const rawRoadmap = await readJsonFile<RawRoadmap>(runArtifacts.roadmapPath);
  const rawPlans = await readJsonFile<RawPlanRow[]>(runArtifacts.plansPath);
  const rawMetrics = await readJsonFile<RawMetrics>(runArtifacts.metricsPath);
  const normalized = normalizeSingleCustomerDemo(rawRoadmap, rawPlans, rawMetrics, runArtifacts);
  if (normalized.summary.decision_status !== REQUIRED_DECISION_STATUS) {
    throw new Error(
      `Live demo customer must be ${REQUIRED_DECISION_STATUS}, got ${normalized.summary.decision_status ?? "unknown"}.`,
    );
  }
  return normalized;
}

export async function getLiveSingleCustomerDemo() {
  const now = Date.now();
  if (cachedDemo && cachedDemo.expiresAt > now) {
    return cachedDemo.data;
  }

  if (!inFlightDemo) {
    inFlightDemo = buildLiveSingleCustomerDemo()
      .then((data) => {
        cachedDemo = {
          data,
          expiresAt: Date.now() + CACHE_TTL_MS,
        };
        return data;
      })
      .finally(() => {
        inFlightDemo = null;
      });
  }

  return inFlightDemo;
}
