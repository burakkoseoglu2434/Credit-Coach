import { z } from "zod";

export const localizedTextSchema = z.object({
  tr: z.string(),
  en: z.string(),
});

export const narrativeCardSchema = z.object({
  label: localizedTextSchema,
  description: localizedTextSchema,
});

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
  step_id: z.string().optional(),
  action_key: z.string(),
  action_class: z.string(),
  action_title: z.string(),
  detail: z.string(),
  time_months: z.number(),
  estimated_cost_usd: z.number(),
  plan_execution_probability: z.number().optional(),
  offer_type: z.string().optional(),
  narrative: z
    .object({
      step_id: z.string(),
      phase_id: z.string().optional(),
      action_key: z.string().nullable().optional(),
      action_group_id: z.string().nullable().optional(),
      action_summary: localizedTextSchema,
      why_this_matters: localizedTextSchema,
      expected_outcome: localizedTextSchema,
      what_happens_if_done: localizedTextSchema,
      what_happens_if_not_done: localizedTextSchema,
      action_timing_hint: localizedTextSchema.optional(),
      offer_narrative: z
        .object({
          offer_explanation: localizedTextSchema,
          why_offered: localizedTextSchema,
          if_accepted: localizedTextSchema,
          if_not_accepted: localizedTextSchema,
          offer_terms_summary: localizedTextSchema.optional(),
        })
        .nullable()
        .optional(),
    })
    .optional(),
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
    decision_status: z.string().optional(),
    approval_ready_now: z.boolean().optional(),
    approval_ready_4w: z.boolean().optional(),
    approval_ready_12w: z.boolean().optional(),
    approval_ready_24w: z.boolean().optional(),
    credit_readiness_stage: z
      .enum(["now", "week_4", "week_12", "week_24", "not_ready_yet"])
      .optional(),
  }),
  phases: z.array(roadmapPhaseSchema),
  checkpoints: z.array(
    z.object({
      checkpoint_id: z.string().optional(),
      week: z.number(),
      checkpoint_label: z.string(),
      predicted_pd: z.number(),
      gate_pass_estimate: z.boolean(),
      note: z.string(),
      approval_ready: z.boolean().optional(),
      narrative: z
        .object({
          checkpoint_id: z.string().optional(),
          week: z.number().optional(),
          expected_state: localizedTextSchema,
          success_condition: localizedTextSchema,
          failure_implication: localizedTextSchema,
          review_action: localizedTextSchema.optional(),
        })
        .optional(),
    }),
  ),
  narrative: z
    .object({
      executive_summary: z.object({
        headline: localizedTextSchema.optional(),
        summary_line: localizedTextSchema.optional(),
        risk_start: narrativeCardSchema,
        recommended_path: narrativeCardSchema,
        offer_status: narrativeCardSchema,
        checkpoint_4w_summary: narrativeCardSchema,
        expected_result: narrativeCardSchema,
        decision_view: narrativeCardSchema,
        time_to_readiness: narrativeCardSchema,
        narrative_confidence: narrativeCardSchema,
      }),
      steps: z.array(
        z.object({
          step_id: z.string(),
          phase_id: z.string(),
          action_key: z.string().nullable().optional(),
          action_group_id: z.string().nullable().optional(),
          action_summary: localizedTextSchema,
          why_this_matters: localizedTextSchema,
          expected_outcome: localizedTextSchema,
          what_happens_if_done: localizedTextSchema,
          what_happens_if_not_done: localizedTextSchema,
          action_timing_hint: localizedTextSchema.optional(),
          offer_narrative: z
            .object({
              offer_explanation: localizedTextSchema,
              why_offered: localizedTextSchema,
              if_accepted: localizedTextSchema,
              if_not_accepted: localizedTextSchema,
              offer_terms_summary: localizedTextSchema.optional(),
            })
            .nullable()
            .optional(),
        }),
      ),
      checkpoints: z.array(
        z.object({
          checkpoint_id: z.string(),
          week: z.number(),
          expected_state: localizedTextSchema,
          success_condition: localizedTextSchema,
          failure_implication: localizedTextSchema,
          review_action: localizedTextSchema.optional(),
        }),
      ),
      reasons: z.array(
        z.object({
          reason_code: z.string(),
          reason_title: localizedTextSchema,
          reason_description: localizedTextSchema,
          remediation_hint: localizedTextSchema,
          reason_severity: z.enum(["low", "moderate", "high"]).optional().nullable(),
        }),
      ),
      technical_reveal: z.object({
        feature_changes: z.array(z.record(z.unknown())),
        explainability_reasons: z.array(z.record(z.unknown())),
        constraints_applied: z.array(z.record(z.unknown())),
        approval_dependencies: z.array(z.record(z.unknown())),
        diagnostic_flags: z.array(z.string()),
        confidence_inputs: z.record(z.unknown()),
        narrative_confidence_label: z.enum(["high", "moderate", "low"]).optional().nullable(),
        narrative_confidence_score: z.number().optional().nullable(),
      }),
    })
    .optional(),
  meta: z
    .object({
      live: z.boolean().optional(),
      source: z.string().optional(),
      run_id: z.string().optional(),
      generated_at: z.string().optional(),
    })
    .optional(),
});

export type DemoIndex = z.infer<typeof demoIndexSchema>;
export type DemoIndexItem = z.infer<typeof demoIndexItemSchema>;
export type SingleCustomerDemo = z.infer<typeof singleCustomerDemoSchema>;
