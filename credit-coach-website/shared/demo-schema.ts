import { z } from "zod";

export const localizedTextSchema = z.object({
  tr: z.string(),
  en: z.string(),
});

export const narrativeCardSchema = z.object({
  label: localizedTextSchema,
  description: localizedTextSchema,
});

export const actionBusinessViewSchema = z.object({
  action_key: z.string().nullable().optional(),
  action_family: z.string().nullable().optional(),
  action_class: z.string().nullable().optional(),
  action_title: z.string().nullable().optional(),
  action_description: z.string().nullable().optional(),
  action_group_id: z.string().nullable().optional(),
});

export const actionTechnicalViewSchema = z.object({
  feature_name: z.string(),
  current_value: z.number().nullable().optional(),
  target_value: z.number().nullable().optional(),
  delta: z.number().nullable().optional(),
  time_months: z.number().nullable().optional(),
  phase_id: z.string().nullable().optional(),
  week_start: z.number().nullable().optional(),
  week_end: z.number().nullable().optional(),
  checkpoint_metric: z.string().nullable().optional(),
});

export const primaryNumericTargetSchema = z.object({
  metric_key: z.string(),
  unit: z.enum([
    "currency",
    "percentage_points",
    "ratio",
    "score_points",
    "months",
    "boolean_state",
    "count",
  ]),
  current_value: z.number().nullable().optional(),
  target_value: z.number(),
  delta_value: z.number(),
  due_month: z.number(),
  direction: z.enum(["decrease", "increase"]),
  generation_notes: z.array(z.string()).optional(),
  raw_generation_basis: z.record(z.unknown()).optional(),
});

export const offerTermsSchema = z.object({
  payment_delta_monthly: z.number().nullable().optional(),
  discount_amount: z.number().nullable().optional(),
  discount_pct: z.number().nullable().optional(),
  term_extension_months: z.number().nullable().optional(),
  interest_rate_delta: z.number().nullable().optional(),
  grace_period_weeks: z.number().nullable().optional(),
  extensions: z.record(z.unknown()).optional(),
});

export const offerContractSchema = z.object({
  offer_type: z.string().nullable().optional(),
  offer_family: z.string().nullable().optional(),
  offer_terms: offerTermsSchema.optional(),
  offer_terms_complete: z.boolean().optional(),
  requires_acceptance: z.boolean().optional(),
  requires_institutional_approval: z.boolean().optional(),
  institutional_approval_state: z
    .enum(["not_required", "approved", "pending", "unknown"])
    .nullable()
    .optional(),
  offer_policy_arm: z.string().nullable().optional(),
  offer_scoring_profile: z.string().nullable().optional(),
  term_generation_rule: z.string().nullable().optional(),
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

export const proofMetricSnapshotSchema = z.object({
  current: z.number(),
  baseline: z.number().optional(),
  delta: z.number().optional(),
  higher_is_better: z.boolean(),
  improved: z.boolean().optional(),
});

export const demoFitAnnotationSchema = z.object({
  demo_representativeness_verdict: z.enum(["representative", "optimistic", "narrow", "misleading"]),
  demo_fit_confidence: z.enum(["strong", "moderate", "weak"]),
  demo_case_segment_share: z.number(),
  product_ready_alignment: z.boolean(),
  narrative: z.string(),
});

export const phase17DeltaSchema = z.object({
  baseline_name: z.string(),
  comparison_story: z.enum([
    "credibility_improved",
    "more_honest_but_narrower",
    "mixed_change",
    "credibility_weakened",
  ]),
  credibility_direction: z.enum(["improved", "mixed", "weaker"]),
  summary: z.string(),
  metrics: z.object({
    product_ready_plan_coverage: proofMetricSnapshotSchema,
    governance_safe_plan_coverage: proofMetricSnapshotSchema,
    execution_aware_value: proofMetricSnapshotSchema,
    weak_4w_health_rate: proofMetricSnapshotSchema,
    reality_gap_flag_rate: proofMetricSnapshotSchema,
  }),
});

export const productConfidenceSnapshotSchema = z.object({
  proof_verdict: z.enum(["working", "promising", "mixed", "not_proven"]),
  proof_confidence: z.enum(["strong", "moderate", "weak"]),
  headline_metrics: z.object({
    product_ready_plan_coverage: proofMetricSnapshotSchema,
    governance_safe_plan_coverage: proofMetricSnapshotSchema,
    execution_aware_value: proofMetricSnapshotSchema,
  }),
  supporting_metrics: z.object({
    weak_4w_health_rate: proofMetricSnapshotSchema,
    delayed_trajectory_rate: z.object({
      current: z.number(),
      higher_is_better: z.boolean(),
    }),
    long_horizon_heavy_rate: z.object({
      current: z.number(),
      higher_is_better: z.boolean(),
    }),
    reality_gap_flag_rate: proofMetricSnapshotSchema,
  }),
  phase17_delta: phase17DeltaSchema,
  demo_fit_annotation: demoFitAnnotationSchema,
  supporting_trust_layer: z.object({
    learning: z.object({
      decision_log_completeness: z.number(),
      learning_ready_share: z.number(),
      reward_90d_coverage: z.number(),
    }),
    ope: z.object({
      comparison_status: z.string(),
      ope_confidence: z.string(),
      preferred_policy_arm: z.string(),
      preferred_policy_signal: z.string(),
    }),
  }),
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
  action_group_id: z.string().optional(),
  detail: z.string().optional(),
  time_months: z.number().optional(),
  estimated_cost_usd: z.number().optional(),
  plan_execution_probability: z.number().optional(),
  action_execution_probability: z.number().optional(),
  action_group_execution_probability: z.number().optional(),
  approval_dependent_probability: z.number().optional(),
  difficulty_score: z.number().optional(),
  difficulty_label: z.string().optional(),
  business_view: actionBusinessViewSchema.optional(),
  technical_view: actionTechnicalViewSchema.optional(),
  primary_numeric_target: primaryNumericTargetSchema.optional(),
  offer_contract: offerContractSchema.optional(),
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
      feasibility_outcome_label: localizedTextSchema.optional(),
      difficulty_label: localizedTextSchema.optional(),
      follow_through_note: localizedTextSchema.optional(),
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
  target_pd: z.number().optional(),
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
    plan_execution_probability: z.number().optional(),
    offer_acceptance_probability: z.number().optional(),
    combined_plan_realization_probability: z.number().optional(),
    trajectory_status: z.string(),
    decision_status: z.enum(["APPROVED", "CONDITIONAL", "REJECTED"]).optional(),
    decision_confidence: z.number().optional(),
    decision_reason_summary: z.string().optional(),
    expected_readiness: z
      .enum(["now", "week_4", "week_12", "week_24", "not_ready", "unknown_review"])
      .optional(),
    conditional_type: z
      .enum(["DATA_ISSUE", "OFFER_GATED", "TIME_GATED", "EXECUTION_GATED"])
      .optional(),
    upgrade_condition: z.string().optional(),
    decision_policy_version: z.string().optional(),
    approval_ready_now: z.boolean().optional(),
    approval_ready_4w: z.boolean().optional(),
    approval_ready_12w: z.boolean().optional(),
    approval_ready_24w: z.boolean().optional(),
    credit_readiness_stage: z
      .enum(["now", "week_4", "week_12", "week_24", "not_ready_yet"])
      .optional(),
    recourse_mode: z.enum(["full", "limited"]).optional(),
    recommendation_mode: z.enum(["actionable", "informational"]).optional(),
    recoverable_flag: z.boolean().optional(),
    recoverability_bucket: z.string().optional(),
    approval_gap: z.number().optional(),
    narrative_type: z.enum(["actionable", "informational"]).optional(),
    informational_subtype: z
      .enum(["structural_limited", "not_currently_actionable"])
      .optional(),
    narrative_contract_version: z.string().optional(),
  }),
  phases: z.array(roadmapPhaseSchema),
  checkpoints: z.array(
    z.object({
      checkpoint_id: z.string().optional(),
      week: z.number(),
      checkpoint_label: z.string(),
      predicted_pd: z.number(),
      gate_pass_estimate: z.boolean(),
      note: z.string().optional(),
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
        follow_through_readiness: narrativeCardSchema.optional(),
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
          feasibility_outcome_label: localizedTextSchema.optional(),
          difficulty_label: localizedTextSchema.optional(),
          follow_through_note: localizedTextSchema.optional(),
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
        primary_numeric_targets: z.array(z.record(z.unknown())).optional(),
        explainability_reasons: z.array(z.record(z.unknown())),
        constraints_applied: z.array(z.record(z.unknown())),
        approval_dependencies: z.array(z.record(z.unknown())),
        diagnostic_flags: z.array(z.string()),
        execution_details: z.record(z.unknown()).optional(),
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
export type ProductConfidenceSnapshot = z.infer<typeof productConfidenceSnapshotSchema>;
