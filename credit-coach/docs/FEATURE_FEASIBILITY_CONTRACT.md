# Feature Feasibility Contract

## Purpose
This contract prevents recourse plans from proposing operationally unrealistic jumps (for example, extreme income/limit changes in a single plan).

## Config
- File: `configs/recourse_feasibility.yaml`
- Activation: `configs/recourse.yaml -> feasibility`

## Enforcement Points
1. Internal planner (`generate_nine_plans`)
2. DiCE candidate actions before scoring/validation

## Rule Keys
- `max_relative_change`: max relative movement per plan from current value.
- `max_abs_increase` / `max_abs_decrease`: hard absolute delta caps.
- `max_abs_increase_per_month` / `max_abs_decrease_per_month`: horizon-scaled movement caps.
- `min_target` / `max_target`: absolute target bounds.
- `freeze_if_current_below` / `freeze_if_current_above`: freeze feature if current value is outside reliable operating range.
- `round_to_int`: force integer target for discrete-like features.

## Precedence
Applied rule is merged as:
1. `defaults`
2. `features.<feature_name>` override

Then clipping runs in this order:
1. freeze rules
2. min/max target bounds
3. relative change bound
4. abs/per-month increase/decrease bounds
5. integer rounding (if enabled)

## Current Strategic Intent
- Keep denied-target mode active, but reject implausible jumps.
- Allow stronger moves on credit limits/income only within bounded plan horizons.
- Freeze low-quality edge cases (example: `last_fico_range_low < 300`) to avoid synthetic artifacts.

## Operational Note
If conversion lift drops after enabling feasibility, first tune:
1. per-feature monthly caps
2. denied-target action budgets
3. DiCE quota (`denied_dice_max_customers`)

Do not relax global safety gates (`CI/reliability/worst_margin`) to compensate.
