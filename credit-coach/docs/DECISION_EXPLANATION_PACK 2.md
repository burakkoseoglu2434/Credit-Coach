# Decision Explanation Pack

Bu dokuman `decision_explanation_pack.json` contract'ini tanimlar.

Artifact audience'i:

- institution-facing
- audit-friendly
- non-legal
- external-safe

Bu artifact operator packet'in sade versiyonu degildir.
Ikisi ayni decision snapshot'tan tureyen farkli audience projection'laridir.

## 1. Canonical Path

Refresh output altinda:

- `tables/decision_explanation_packs/<customer_dir>/decision_explanation_pack.json`

Destekleyici markdown:

- `tables/decision_explanation_packs/<customer_dir>/decision_explanation_pack.md`

## 2. Minimum Fields

- `contract_version`
- `decision_id`
- `customer_id`
- `decision_outcome`
- `external_decision_only`
- `one_line_decision_reason`
- `structured_numeric_drivers`
- `driver_methodology_note`
- `upgrade_condition`
- `expected_readiness`
- `adverse_action_friendly_reasons`
- `policy_version`
- `policy_effective_at`
- `artifact_generated_at`
- `qa_status`
- `qa_stamp`
- `human_review_required`
- `disclaimer`

## 3. Hard Guardrails

### External-only states

Bu artifact yalnizca su karar vocabulary'sini kullanir:

- `APPROVED`
- `CONDITIONAL`
- `REJECTED`

`NEEDS_REVIEW` asla gosterilmez.

### Shared-truth rule

Explanation pack su alanlarda operator packet ile drift etmez:

- `decision_id`
- `policy_version`
- external decision outcome
- one-line decision reason
- `expected_readiness`
- `upgrade_condition`

### No engine dump

Su alanlar explanation pack icine alinmaz:

- raw gate trace
- internal decision state
- candidate policy tables
- planner debug detail

## 4. Numeric Drivers

Driver sunumu:

- numeric-first
- target-oriented
- institution-safe

Ornek:

- `utilization: 82 -> 50`
- `execution_strength: 0.38 -> 0.50`

Driver listesi:

- tam feature dump degildir
- owned decision payload'tan tureyen aciklanabilir ozetlerdir

## 5. Adverse-Action-Compatible Reasons

Reason seti:

- short
- standardized
- controlled

Ama bu artifact:

- legal opinion degildir
- compliance automation degildir
- institution review yerine gecmez

## 6. Boundary Statements

Recommended disclaimer posture:

- institution-facing explanatory support
- not a legal opinion
- not compliance automation
- does not replace institution review

## 7. Relationship To Other Artifacts

Canonical ownership:

- decision payload -> truth owner
- operator packet -> internal review lens
- explanation pack -> external-safe institution lens

Related docs:

- [PILOT_PACKAGE_SCHEMA.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/PILOT_PACKAGE_SCHEMA.md)
- [PILOT_EXECUTION_GUIDE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/PILOT_EXECUTION_GUIDE.md)
