import { z } from "zod";

export const metricRecordSchema = z.object({
  label: z.string(),
  value: z.union([z.string(), z.number()]),
  change: z.string().optional(),
  hint: z.string().optional(),
});

export const artifactRefSchema = z.object({
  name: z.string(),
  description: z.string(),
  type: z.enum(["json", "csv", "markdown"]),
});

export const demoIndexItemSchema = z.object({
  slug: z.string(),
  title: z.string(),
  category: z.string(),
  summary: z.string(),
  type: z.enum(["json", "markdown"]),
});

export const demoIndexSchema = z.object({
  company: z.literal("Kuantitive"),
  product: z.literal("credit-coach"),
  items: z.array(demoIndexItemSchema),
});

export const roadmapStepSchema = z.object({
  action_key: z.string(),
  action_class: z.string(),
  action_title: z.string(),
  detail: z.string(),
  time_months: z.number(),
  estimated_cost_usd: z.number(),
  plan_execution_probability: z.number().optional(),
  offer_type: z.string().optional(),
});

export const roadmapPhaseSchema = z.object({
  phase_id: z.string(),
  phase_title: z.string(),
  target_window_weeks: z.string(),
  target_pd: z.number(),
  steps: z.array(roadmapStepSchema),
});

export const singleCustomerDemoSchema = z.object({
  customer: z.object({
    customer_id: z.string(),
    profile: z.string(),
    segment: z.string(),
    risk_band: z.string(),
    income_band: z.string(),
  }),
  summary: z.object({
    base_pd: z.number(),
    target_pd_4w: z.number(),
    target_pd_12w: z.number(),
    target_pd_24w: z.number(),
    plan_execution_probability: z.number(),
    offer_acceptance_probability: z.number(),
    combined_plan_realization_probability: z.number(),
    trajectory_status: z.string(),
  }),
  phases: z.array(roadmapPhaseSchema),
  checkpoints: z.array(
    z.object({
      week: z.number(),
      checkpoint_label: z.string(),
      predicted_pd: z.number(),
      gate_pass_estimate: z.boolean(),
      note: z.string(),
    }),
  ),
});

export type DemoIndex = z.infer<typeof demoIndexSchema>;
export type DemoIndexItem = z.infer<typeof demoIndexItemSchema>;
export type SingleCustomerDemo = z.infer<typeof singleCustomerDemoSchema>;
