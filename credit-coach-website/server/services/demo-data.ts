import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  demoIndexSchema,
  productConfidenceSnapshotSchema,
  singleCustomerDemoSchema,
} from "../../shared/demo-schema.js";
import { getLiveSingleCustomerDemo } from "./live-demo.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..", "..");
const demoDataDir = path.resolve(rootDir, "demo-data");

type DemoItem = {
  slug: string;
  title: string;
  category: string;
  summary: string;
  type: "json" | "markdown";
  filename: string;
};

const items: DemoItem[] = [
  {
    slug: "single-customer-roadmap",
    title: "Single Customer Roadmap",
    category: "demo",
    summary: "A phased improvement plan with actions, checkpoint targets, and institution-side offer context.",
    type: "json",
    filename: "single_customer_roadmap.json",
  },
  {
    slug: "portfolio-batch-summary",
    title: "Portfolio Batch Summary",
    category: "proof",
    summary: "The core uplift, risk, and trajectory metrics for a denied-customer cohort.",
    type: "json",
    filename: "batch_summary.json",
  },
  {
    slug: "product-confidence-snapshot",
    title: "Product Confidence Snapshot",
    category: "proof",
    summary: "Executive proof verdict, confidence, Phase 17 delta, and trust annotations for buyer-facing proof surfaces.",
    type: "json",
    filename: "product_confidence_snapshot.json",
  },
  {
    slug: "candidate-quality",
    title: "Candidate Quality Summary",
    category: "proof",
    summary: "Diversity and source-mix quality for recommendation candidates.",
    type: "json",
    filename: "candidate_quality_summary.json",
  },
  {
    slug: "action-realism",
    title: "Action Realism Summary",
    category: "proof",
    summary: "Shows whether recommendation actions are feasible, clipped, rejected, or approval-dependent.",
    type: "json",
    filename: "action_realism_summary.json",
  },
  {
    slug: "behavior-aware",
    title: "Behavior-Aware Summary",
    category: "proof",
    summary: "Execution likelihood and partial-execution metrics for recommended plans.",
    type: "json",
    filename: "behavior_aware_summary.json",
  },
  {
    slug: "trajectory",
    title: "Trajectory Summary",
    category: "proof",
    summary: "Short-term-first phased trajectory performance and replan signals.",
    type: "json",
    filename: "trajectory_summary.json",
  },
  {
    slug: "offer-optimization",
    title: "Offer Optimization Summary",
    category: "demo",
    summary: "Institution-side offer mix, acceptance probability, and business proxy deltas.",
    type: "json",
    filename: "offer_optimization_summary.json",
  },
  {
    slug: "decision-logging",
    title: "Decision Logging Summary",
    category: "learning",
    summary: "Learning-grade coverage of decision metadata, propensities, and reason codes.",
    type: "json",
    filename: "decision_logging_summary.json",
  },
  {
    slug: "outcome-ingestion",
    title: "Outcome Ingestion Summary",
    category: "learning",
    summary: "Outcome completeness and 90-day learning readiness coverage.",
    type: "json",
    filename: "outcome_ingestion_summary.json",
  },
  {
    slug: "off-policy-evaluation",
    title: "Off Policy Evaluation",
    category: "learning",
    summary: "IPS / DR comparative policy evidence using approval, default, and margin proxies.",
    type: "json",
    filename: "off_policy_evaluation.json",
  },
  {
    slug: "milestone-acceptance",
    title: "Milestone Acceptance Summary",
    category: "governance",
    summary: "Machine-readable release and governance decision summary.",
    type: "json",
    filename: "milestone_acceptance_summary.json",
  },
  {
    slug: "milestone-review",
    title: "Milestone Acceptance Review",
    category: "governance",
    summary: "Human-readable review that explains decision, telemetry, learning loop, and pack completeness.",
    type: "markdown",
    filename: "milestone_acceptance_review.md",
  },
];

export function getDemoIndex() {
  return demoIndexSchema.parse({
    company: "Kuantitive",
    product: "credit-coach",
    items: items.map(({ slug, title, category, summary, type }) => ({
      slug,
      title,
      category,
      summary,
      type,
    })),
  });
}

export async function getDemoPayload(slug: string) {
  const item = items.find((entry) => entry.slug === slug);
  if (!item) {
    return null;
  }

  if (slug === "single-customer-roadmap") {
    try {
      return {
        ...item,
        content: await getLiveSingleCustomerDemo(),
      };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.warn("Falling back to static single customer demo:", error);
    }
  }

  const fullPath = path.resolve(demoDataDir, item.filename);
  const raw = await fs.readFile(fullPath, "utf-8");
  if (item.type === "markdown") {
    return {
      ...item,
      content: raw,
    };
  }

  const parsed = JSON.parse(raw);
  return {
    ...item,
    content:
      slug === "product-confidence-snapshot"
        ? productConfidenceSnapshotSchema.parse(parsed)
        : slug === "single-customer-roadmap"
          ? singleCustomerDemoSchema.parse(parsed)
          : parsed,
  };
}
