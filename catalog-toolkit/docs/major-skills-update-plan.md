# Major Skills Update Plan (Square + Catalog Toolkit)

## Objective

Standardize Square category operations, visibility policy, and change monitoring so every agent/skill can safely perform catalog updates with version-locked API compliance (`2026-01-22`).

## Current Cleanup State (as of 2026-02-16)

- Food merge complete:
  - `Chips & Crisps`, `Cookies & Sweets`, `Drinks`, `Asian Imports` -> `Food & Pantry`
- Legacy food categories are empty and hidden.
- `The New Finds` currently has 10 items (intake cap target met).
- Active online sites are published and categories with items are visible on active channels.
- Required scaffold categories exist:
  - `Food & Pantry`
  - `The General Store`
  - `The Vintage Market`
  - `New Arrivals`

## Immediate Skill Hygiene Gaps (from metadata audit)

- `claude-skills-loader`: missing `metadata.updated`
- `linear`: missing parsed `metadata.version` and `metadata.updated`
- `pdf`: missing parsed `metadata.version` and `metadata.updated`
- `playwright`: missing parsed `metadata.version` and `metadata.updated`
- `screenshot`: missing parsed `metadata.version` and `metadata.updated`

## Skill Update Scope

### 1) `catalog-classifier` (highest impact)

Update taxonomy rules to align with current storefront model:

- Keep type categories (Books & Paper, Collectibles, Wellness, etc.)
- Replace snack routing with `Food & Pantry` (not the four legacy food categories)
- Keep tier split:
  - `The New Finds` for vintage intake
  - `New Arrivals` for general-store intake
- Add explicit top-level separator logic:
  - General Store vs Vintage Market routing

## 2) `rg-item-update`

Add deterministic batch operations backed by `catalog-toolkit`:

- `merge_food_categories.py`
- `catalog_cleanup_audit.py`
- `compliance_check.py`

Add an explicit post-write verification gate:

- run cleanup audit
- run square-cache sync
- verify changed SKUs/categories in cache

## 3) `rg-full-auto`

Wire Phase 1 category assignment to the updated classifier output:

- enforce primary type category + tier category
- enforce reporting category = primary type category
- apply New Finds vs New Arrivals by storefront branch

## 4) `square-cache`

Add operational references for new toolkit scripts:

- nightly/after-mutation audit command
- recommended diff review (`changes --since <date>`)
- webhook monitor handoff for near-real-time alerts

## 5) New skill: `square-catalog-ops` (recommended)

Create a dedicated operational skill that wraps:

- compliance checks
- category merge/cleanup audit
- channel/site assignment checks
- webhook subscription bootstrap/testing

This avoids overloading `rg-item-update` with admin-level catalog governance.

## 6) New skill: `square-webhook-monitor` (recommended)

Promote webhook scaffold into an operational skill:

- run FastAPI monitor
- validate signatures
- persist events
- alert on catalog version updates and subscription failures

## Execution Order

1. Normalize skill metadata contract on all active skills (missing `version/updated` fields first).
2. Freeze taxonomy IDs and naming in one canonical reference file.
3. Update `catalog-classifier`.
4. Update `rg-item-update` + `rg-full-auto`.
5. Add `square-catalog-ops` skill.
6. Add `square-webhook-monitor` skill.
7. Update `square-cache` docs + runbook links.
8. Run end-to-end validation with sandbox/test items, then production spot-check.

## Validation Gates

For each updated skill:

1. Metadata contract passes (`name`, `description`, `metadata.version/author/updated`).
2. All Square writes use `Square-Version: 2026-01-22`.
3. `scripts/compliance_check.py` passes.
4. `scripts/catalog_cleanup_audit.py --fail-on-issues` passes.
5. `square_cache.sh sync` shows expected changes only.

## Risks and Controls

- Risk: taxonomy drift between skills.
  - Control: single source-of-truth category map consumed by all skills.
- Risk: hidden categories after write operations.
  - Control: mandatory cleanup audit post-write.
- Risk: silent API-version drift.
  - Control: compliance check in every operational runbook.
- Risk: webhook blind spots.
  - Control: subscription test + signature key rotation cadence.
