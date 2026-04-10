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
const PYTHON_BINS = ["python", "python3"];
const DEMO_DB_URL = "sqlite:///./credit_coach_demo_state.db";

type DemoCaseExpectation = {
  narrative_type?: "actionable" | "informational";
  recourse_mode?: "full" | "limited";
};

type DemoCaseRegistry = {
  version: string;
  default_case_id: string;
  cases: Array<{
    id: string;
    customer_id: string;
    row_index: number;
    expected?: DemoCaseExpectation;
  }>;
};

const DEFAULT_DEMO_CASE_REGISTRY: DemoCaseRegistry = {
  version: "v2.5",
  default_case_id: "actionable_full",
  cases: [
    {
      id: "actionable_full",
      customer_id: "website_demo_actionable",
      row_index: 351,
      expected: { narrative_type: "actionable", recourse_mode: "full" },
    },
    {
      id: "informational_mid_risk",
      customer_id: "website_demo_informational",
      row_index: 109,
      expected: { narrative_type: "informational", recourse_mode: "limited" },
    },
  ],
};

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

const cachedDemos = new Map<string, CachedDemo>();
const inFlightDemos = new Map<string, Promise<SingleCustomerDemo>>();

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

function demoCasesPath() {
  return path.resolve(websiteRootDir(), "demo-data", "demo-cases.json");
}

async function loadDemoCaseRegistry(): Promise<DemoCaseRegistry> {
  try {
    const raw = await fs.readFile(demoCasesPath(), "utf-8");
    const parsed = JSON.parse(raw) as Partial<DemoCaseRegistry>;
    if (!parsed || typeof parsed !== "object" || !Array.isArray(parsed.cases)) {
      return DEFAULT_DEMO_CASE_REGISTRY;
    }
    const defaultCaseId =
      typeof parsed.default_case_id === "string" && parsed.default_case_id.trim()
        ? parsed.default_case_id.trim()
        : DEFAULT_DEMO_CASE_REGISTRY.default_case_id;
    const cases = parsed.cases
      .filter((entry) => entry && typeof entry === "object")
      .map((entry) => entry as DemoCaseRegistry["cases"][number])
      .filter(
        (entry) =>
          typeof entry.id === "string" &&
          entry.id.trim() &&
          typeof entry.customer_id === "string" &&
          entry.customer_id.trim() &&
          typeof entry.row_index === "number" &&
          Number.isFinite(entry.row_index),
      );
    if (cases.length === 0) {
      return DEFAULT_DEMO_CASE_REGISTRY;
    }
    return {
      version: typeof parsed.version === "string" && parsed.version.trim() ? parsed.version.trim() : "v2.5",
      default_case_id: defaultCaseId,
      cases,
    };
  } catch {
    return DEFAULT_DEMO_CASE_REGISTRY;
  }
}

function pickDemoCase(registry: DemoCaseRegistry, requestedId: string | undefined) {
  const normalized = typeof requestedId === "string" ? requestedId.trim() : "";
  const candidateId = normalized || registry.default_case_id || DEFAULT_DEMO_CASE_REGISTRY.default_case_id;
  return (
    registry.cases.find((entry) => entry.id === candidateId) ??
    registry.cases.find((entry) => entry.id === registry.default_case_id) ??
    registry.cases[0]
  );
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
  const pythonPath = [
    path.resolve(creditCoachRootDir(), "src"),
    process.env.PYTHONPATH,
  ]
    .filter(Boolean)
    .join(path.delimiter);
  let lastError: Error | null = null;

  for (const pythonBin of PYTHON_BINS) {
    try {
      await execFileAsync(pythonBin, args, {
        cwd: creditCoachRootDir(),
        env: {
          ...process.env,
          DB_URL: DEMO_DB_URL,
          MPLCONFIGDIR: mplConfigDir,
          PYTHONPATH: pythonPath,
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

function toOptionalNumber(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function normalizeCreditReadinessStageValue(
  value: unknown,
): SingleCustomerDemo["summary"]["credit_readiness_stage"] | undefined {
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
  return undefined;
}

function normalizeRecourseMode(
  value: unknown,
): SingleCustomerDemo["summary"]["recourse_mode"] | undefined {
  const normalized = toStringValue(value).trim().toLowerCase();
  if (normalized === "full" || normalized === "limited") {
    return normalized as SingleCustomerDemo["summary"]["recourse_mode"];
  }
  return undefined;
}

function normalizeRecommendationMode(
  value: unknown,
): SingleCustomerDemo["summary"]["recommendation_mode"] | undefined {
  const normalized = toStringValue(value).trim().toLowerCase();
  if (normalized === "actionable" || normalized === "informational") {
    return normalized as SingleCustomerDemo["summary"]["recommendation_mode"];
  }
  return undefined;
}

function normalizeNarrativeType(
  value: unknown,
): SingleCustomerDemo["summary"]["narrative_type"] | undefined {
  const normalized = toStringValue(value).trim().toLowerCase();
  if (normalized === "actionable" || normalized === "informational") {
    return normalized as SingleCustomerDemo["summary"]["narrative_type"];
  }
  return undefined;
}

function normalizeInformationalSubtype(
  value: unknown,
): SingleCustomerDemo["summary"]["informational_subtype"] | undefined {
  const normalized = toStringValue(value).trim().toLowerCase();
  if (normalized === "structural_limited" || normalized === "not_currently_actionable") {
    return normalized as SingleCustomerDemo["summary"]["informational_subtype"];
  }
  return undefined;
}

function normalizeSingleCustomerDemo(
  rawRoadmap: RawRoadmap,
  rawMetrics: RawMetrics,
  runArtifacts: RunArtifacts,
): SingleCustomerDemo {
  const summary = toRecord(rawRoadmap.summary) ?? {};
  const checkpoint4w = getCheckpoint(rawRoadmap, 4);
  const checkpoint12w = getCheckpoint(rawRoadmap, 12);
  const checkpoint24w = getCheckpoint(rawRoadmap, 24);
  const stepNarrativeMap = new Map(
    (rawRoadmap.narrative?.steps ?? []).map((entry) => [toStringValue(entry.step_id), entry] as const),
  );
  const checkpointNarrativeMap = new Map(
    (rawRoadmap.narrative?.checkpoints ?? []).map((entry) => [toStringValue(entry.checkpoint_id), entry] as const),
  );

  const phases = (rawRoadmap.phases ?? []).map((phase) => {
    return {
      phase_id: toStringValue(phase.phase_id),
      phase_title: toStringValue(phase.phase_title),
      target_window_weeks: toStringValue(phase.target_window_weeks),
      target_pd: toOptionalNumber(phase.target_pd),
      steps: (phase.steps ?? []).map((step) => {
        const stepId = toStringValue(step.step_id);
        return {
          step_id: stepId || undefined,
          action_key: toStringValue(step.action_key),
          action_class: toStringValue(step.action_class),
          action_title: toStringValue(step.action_title),
          action_group_id: toStringValue(step.action_group_id) || undefined,
          time_months: toOptionalNumber(step.time_months),
          estimated_cost_usd: toOptionalNumber(step.estimated_cost_usd),
          action_execution_probability: toOptionalNumber(step.action_execution_probability),
          action_group_execution_probability: toOptionalNumber(step.action_group_execution_probability),
          approval_dependent_probability: toOptionalNumber(step.approval_dependent_probability),
          difficulty_score: toOptionalNumber(step.difficulty_score),
          difficulty_label: toStringValue(step.difficulty_label) || undefined,
          business_view: toBusinessView(step.business_view),
          technical_view: toTechnicalView(step.technical_view),
          primary_numeric_target: toPrimaryNumericTarget(step.primary_numeric_target),
          offer_contract: toOfferContract(step.offer_contract),
          offer_type: toStringValue(step.offer_type) || undefined,
          narrative: stepId ? stepNarrativeMap.get(stepId) : undefined,
        };
      }),
    };
  });

  const expectedReadiness = normalizeExpectedReadiness(summary.expected_readiness);
  const creditReadinessStage = normalizeCreditReadinessStageValue(summary.credit_readiness_stage);
  const decisionStatus = normalizeDecisionStatus(summary.decision_status ?? rawMetrics.decision_status);
  const decisionConfidence = toOptionalNumber(summary.decision_confidence);

  const content: SingleCustomerDemo = {
    customer: {
      customer_id: toStringValue(rawRoadmap.customer_id, "website_demo_customer"),
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
      trajectory_status: toStringValue(summary.trajectory_status ?? rawRoadmap.trajectory_status, "on_track"),
      decision_status: decisionStatus,
      decision_confidence: decisionConfidence,
      decision_reason_summary: toStringValue(summary.decision_reason_summary) || undefined,
      expected_readiness: expectedReadiness,
      conditional_type: normalizeConditionalType(summary.conditional_type),
      upgrade_condition: toStringValue(summary.upgrade_condition) || undefined,
      decision_policy_version: toStringValue(summary.decision_policy_version) || undefined,
      plan_execution_probability: toOptionalNumber(summary.plan_execution_probability),
      offer_acceptance_probability: toOptionalNumber(summary.offer_acceptance_probability),
      combined_plan_realization_probability: toOptionalNumber(summary.combined_plan_realization_probability),
      approval_ready_now: summary.approval_ready_now === undefined ? undefined : toBoolean(summary.approval_ready_now),
      approval_ready_4w: summary.approval_ready_4w === undefined ? undefined : toBoolean(summary.approval_ready_4w),
      approval_ready_12w: summary.approval_ready_12w === undefined ? undefined : toBoolean(summary.approval_ready_12w),
      approval_ready_24w: summary.approval_ready_24w === undefined ? undefined : toBoolean(summary.approval_ready_24w),
      credit_readiness_stage: creditReadinessStage,
      recourse_mode: normalizeRecourseMode(summary.recourse_mode),
      recommendation_mode: normalizeRecommendationMode(summary.recommendation_mode),
      recoverable_flag: summary.recoverable_flag === undefined ? undefined : toBoolean(summary.recoverable_flag),
      recoverability_bucket: toStringValue(summary.recoverability_bucket) || undefined,
      approval_gap: toOptionalNumber(summary.approval_gap),
      narrative_type: normalizeNarrativeType(summary.narrative_type),
      informational_subtype: normalizeInformationalSubtype(summary.informational_subtype),
      narrative_contract_version: toStringValue(summary.narrative_contract_version) || undefined,
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
      note: undefined,
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

async function buildLiveSingleCustomerDemo(demoCase: DemoCaseRegistry["cases"][number]) {
  await ensureWebsiteDemoAssets();

  const recourseStartMs = Date.now();
  await runPythonCommand(
    [
      "-m",
      "credit_coach.cli.run_recourse",
      "--customer_id",
      demoCase.customer_id,
      "--row_index",
      String(demoCase.row_index),
      "--base_config",
      "configs/website_demo.yaml",
      "--model_config",
      "configs/model_website_demo.yaml",
    ],
    "Website demo recourse run",
  );

  const runArtifacts = await findLatestRunArtifacts(recourseStartMs - 1000);
  const rawRoadmap = await readJsonFile<RawRoadmap>(runArtifacts.roadmapPath);
  const rawMetrics = await readJsonFile<RawMetrics>(runArtifacts.metricsPath);
  const normalized = normalizeSingleCustomerDemo(rawRoadmap, rawMetrics, runArtifacts);
  const expected = demoCase.expected;
  if (expected?.narrative_type && normalized.summary.narrative_type !== expected.narrative_type) {
    throw new Error(
      `Live demo case '${demoCase.id}' expected narrative_type=${expected.narrative_type}, got ${normalized.summary.narrative_type ?? "unknown"}.`,
    );
  }
  if (expected?.recourse_mode && normalized.summary.recourse_mode !== expected.recourse_mode) {
    throw new Error(
      `Live demo case '${demoCase.id}' expected recourse_mode=${expected.recourse_mode}, got ${normalized.summary.recourse_mode ?? "unknown"}.`,
    );
  }
  return normalized;
}

export async function getLiveSingleCustomerDemo(requestedCaseId?: string) {
  const registry = await loadDemoCaseRegistry();
  const demoCase = pickDemoCase(registry, requestedCaseId);
  const cacheKey = demoCase.id;

  const now = Date.now();
  const cached = cachedDemos.get(cacheKey);
  if (cached && cached.expiresAt > now) {
    return cached.data;
  }

  const inFlight = inFlightDemos.get(cacheKey);
  if (inFlight) {
    return inFlight;
  }

  const promise = buildLiveSingleCustomerDemo(demoCase)
      .then((data) => {
        cachedDemos.set(cacheKey, {
          data,
          expiresAt: Date.now() + CACHE_TTL_MS,
        });
        return data;
      })
      .finally(() => {
        inFlightDemos.delete(cacheKey);
      });
  inFlightDemos.set(cacheKey, promise);
  return promise;
}
