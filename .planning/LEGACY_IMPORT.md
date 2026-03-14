# Legacy Import Manifest

## Purpose

This file records how pre-GSD documentation was migrated into the `.planning/` structure on 2026-03-14. The goal is to preserve all historical planning, research, execution, and operations context while making the repository look and behave like a GSD-managed project.

## Import Layout

- `.planning/research/legacy/`
  - Research notes, backlog studies, redesign plans, and roadmap-style planning documents
- `.planning/archive/legacy-reports/`
  - Execution reports, sprint reports, KPI reports, and implementation logs
- `.planning/references/legacy/`
  - Operational references, onboarding material, agent guides, and standing contracts/runbooks

## Source-to-Destination Rules

- Repo-root files matching `CREDIT_COACH*` were imported into one of the legacy subdirectories above based on document purpose.
- Files under `credit-coach/docs/*.md` were imported into one of the same legacy subdirectories based on whether they were research/plans, reports, or standing references.
- After import verification, originals were removed from their previous locations so `.planning/` became the authoritative home.

## Notes

- This was a brownfield migration, not a fresh greenfield initialization.
- Core GSD files (`PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, `config.json`) were synthesized from the imported materials.
- Historical filenames were preserved to keep existing references recognizable.
