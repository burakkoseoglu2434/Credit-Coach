# Golden set v1

A frozen regression snapshot of `decide()` under policy **v1**. It answers "did the code change?",
**not** "is the decision right?". Correctness evidence lives in the rule tests, the Hypothesis
properties and the rule coverage report. A green snapshot only means the output is byte-identical to
what was recorded.

## Files
| File | Content |
|---|---|
| `inputs_v1.jsonl` | 198 real calibration-split applications + 7 synthetic v1 scenarios, frozen inputs |
| `expected_v1.jsonl` | canonical decision output for each input (byte-compared) |
| `variants_inputs.jsonl` / `variants_expected.jsonl` | **policy-variant** records, each with its own policy and a `VARIANT:` label |
| `MANIFEST.json` | SHA-256 of the four files and of `configs/policy/v1.yaml` |
| `CHANGELOG.md` | one line per intentional snapshot update |

Inputs carry `p_low/p_point/p_high`, `ham_skor` and the application features. The tests never run the
model, the calibrator or raw data, so they run in CI. The calibrator was fit on this same split, so
the intervals are in-sample: this set checks the decision layer, not calibration quality.

## Selection rule (run once, `python -m credit_coach.golden generate`)
Source: **calibration split only** (the test split is never used). `numpy.random.default_rng(42)`.
Strata are taken in this order; each skips rows already chosen:
1. extremes: 10 lowest and 10 highest `ham_skor` (no sampling)
2. `near_threshold_3band`: `|p_point - threshold| <= 3 x band`, up to 40
3. `interval_straddles`: `p_low <= threshold <= p_high`, up to 30 (only 8 more existed)
4. `weak_support_zone`: `ham_skor` inside a v1 weak-support range, up to 30
5. `score_decile_0..9`: 10 per decile of `ham_skor` (100)

`generate` refuses to overwrite. `pytest` re-derives the selection from raw data when it is available
and requires identical bytes (skipped in CI, where raw data is absent).

## What v1 actually does here (counts for the 198 real records)
APPROVED 63, REJECTED 125, CONDITIONAL (NEEDS_REVIEW via R2) 10. Rules fired: R4 63, R6 125, R2 10.
`REJECTED` exists in v1 through **R6** (not approved, no plan information). What does not exist in v1 is
the **hard reject** (`R1`, `ret_esigi` is null) and `R3` never fires at the v1 threshold. Those two
rules appear only in the variant files.

## Policy-variant records are NOT v1 behaviour
`variants_*` run under altered policies: `ret_esigi = 0.30` (R1) and a weak-support range around the
threshold (R3), plus the named synthetic scenarios that need a variant. They are labelled
`VARIANT:...` and kept in separate files so nobody reads them as v1 behaviour. Golden v2 (week 4)
will carry the real v2 policy.

## Limits of this snapshot
- Regression only; it cannot tell whether v1 is a good policy.
- Real near-threshold records are few (10 of 198 reach R2), so some code changes (for example widening
  the band) only show up in the variant and synthetic records. Mutation check: widening the R2 band
  changed no real record, only a variant.
- Bound to policy v1's file hash. If `v1.yaml` changes the test fails: v1 is frozen, make golden v2.

## Changing the snapshot (deliberately)
```
python -m credit_coach.golden check      # shows the diff, exit 1 on any difference
python -m credit_coach.golden update --accept-diff --reason "why this change is intentional"
```
`update` prints the diff, refuses without `--accept-diff` and a non-empty `--reason`, appends the
reason to `CHANGELOG.md`, and refuses entirely when policy v1 changed. The commit message must
contain "change is intentional because ...".
