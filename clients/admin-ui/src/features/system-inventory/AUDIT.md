# System Inventory — UI Audit

## Route Page: `/system-inventory`

### Section: Dashboard Widget (GovernanceHealthDashboard)

| Aspect             | Detail                                                                                         |
| ------------------ | ---------------------------------------------------------------------------------------------- |
| **Job to be done** | Show overall governance posture at a glance — score, pillar breakdown, trends, recent activity |
| **Data source**    | `GovernanceHealthData` from `computeGovernanceHealth()` in `utils.ts`                          |
| **Components**     | GovernanceScoreCard (donut + key), stacked AreaChart (trend), activity feed                    |

#### Panel 1: Inventory Health (Donut + Key)

- **Score**: Average of 4 pillar percentages. Currently **hardcoded** at 58/92/84/66 = 75.
- **Donut**: Padded-angle pie chart with rounded corners. Each pillar gets 25% of the ring. Filled portion = pillar score, unfilled = neutral-100. 100% pillars skip the gray segment.
- **Key**: 2x2 grid with brand-colored dots (terracotta, sandstone, olive, minos).

**OPEN ISSUE — HARDCODED SCORES**: `computeGovernanceDimensions()` calculates real values from system data but the return statement (line 62-67 of `utils.ts`) **ignores computed values** and returns hardcoded numbers. The computed `annotationScore`, `complianceScore`, `purposeScore`, `stewardScore` are dead code. **Fix**: Remove hardcoded return, use the computed values.

#### Panel 2: Health Over Time (Stacked Area Chart) — RESOLVED

- **Data model**: Each pillar contributes `score/4` so they stack to the overall score. March values: 14.5 + 23 + 21 + 16.5 = 75 — matches the donut exactly.
- **Y-axis**: 0-100. Stacked total rises from ~34 to ~75 over 6 months.
- **Previous issue**: Raw contribution counts (2-22 range) that didn't match pillar percentages. **Now fixed** — data model is honest and visually accurate.
- **Remaining**: Data is still hardcoded mock. When real, should derive from `computeGovernanceDimensions()` run over historical snapshots.

#### Panel 3: Recent Activity

- **Data**: Hardcoded `ACTIVITY` array with message, time, steward avatar.
- **No issues**: Display-only mock data, correctly structured.

### Section: System Card Grid

| Aspect               | Detail                                                                                                             |
| -------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **Job to be done**   | Browse systems, identify which need attention, navigate to detail                                                  |
| **Data source**      | `MOCK_SYSTEMS` filtered by `useSystemInventory` hook                                                               |
| **What's indicated** | Health status (green/orange/red), purpose tags, annotation progress (circular, stoplight colors), steward presence |

- Cards split into "Needs attention" (issue_count > 0) and "Healthy" with assessment-style section headers.
- Background: corinth. Purpose tags: neutral-100. No steward: gray secondary text.
- **No issues**: Layout is clear and functional.

### Section: Filters

- Health filter: "Needs attention" / "Healthy".
- Type, group, purpose filters from computed options.
- **No issues**.

---

## Detail Page: `/system-inventory/[id]`

### Page Structure (top to bottom)

1. Breadcrumb + System Header (logo, name, type, department, responsibility, delete + export buttons)
2. AI Briefing Banner (bg-default, sparkle icon, natural language summary + issue CTAs)
3. Metric Cards row (System Health, Capabilities, Privacy Requests, Datasets)
4. Tabs: Overview, Datasets, History, Assets, Advanced

### Section: System Header

- Logo via `getBrandIconUrl` or `logoUrl` override, name, subtitle with type/department/responsibility.
- **Actions**: Trash can (delete with confirmation modal) + Export CSV button.
- **No issues**.

### Section: AI Briefing Banner

- **Job to be done**: Surface what a steward needs to know — system summary + actionable issues.
- **Data**: `buildRichBriefing()` generates natural language from system properties. `getIssues()` derives action items.
- **Background**: bg-default. Sparkle icon. Issues shown as error tags with text button CTAs.
- **No issues**: Well-structured, dismissible (sessionStorage).

### Section: Metric Cards (SystemDetailDashboardV2)

| Card                 | Data Source                       | What's shown                                                                                                                 |
| -------------------- | --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **System Health**    | `computeSystemDimensions(system)` | Padded-angle donut with score inside. 2x2 pillar key. Uses **real computed values**.                                         |
| **Capabilities**     | `getSystemCapabilities(system)`   | Tag list with Carbon icons (DSARs, Monitoring, Consent, Integrations, Classification). Read-only, derived from integrations. |
| **Privacy Requests** | `system.privacyRequests`          | Open count, closed count, avg access days.                                                                                   |
| **Datasets**         | `system.datasets`                 | Count, total fields, total collections.                                                                                      |

- All cards use `flex-1` for equal responsive widths. Background: neutral-75.
- **Previous issue (RESOLVED)**: Classification card was orphaned from governance score. Replaced with Capabilities. Classification data lives solely in the Classification Progress section below.

### Section: About (Overview tab)

- **Job to be done**: Quick reference for system identity.
- **Layout**: 2-column grid — Type/Responsibility, Department/Roles, Group/Description. Values are semi-bold.
- **Edit**: Opens a full modal with properly sized inputs.
- **No issues**.

### Section: Governance (Overview tab)

- **Job to be done**: Manage purposes and steward assignments.
- **Description**: Explains role of purposes (legal basis) and stewards (accountability).
- **Layout**: Two equal columns — Purposes (tags + picker modal) and Stewards (avatars + picker modal).
- **Purpose picker**: Searchable table with Purpose, Data Use, Description columns. Filter by data use.
- **Steward picker**: Searchable table with Name (avatar), Email, Role columns.
- **No issues**.

### Section: Integrations (Overview tab)

- **Job to be done**: Manage connections to this system for DSR, monitoring, consent, classification.
- **Description**: Explains what integrations do (DSR execution, schema monitoring, consent enforcement).
- **Layout**: Full-width table with Name, Type, Status (tag), Last tested, Capabilities, Actions.
- **Actions**: Edit (opens config modal with BigQuery keyfile creds, project ID, dataset, access level, capabilities), Test, Remove (confirmation modal).
- **Add**: Picker modal with searchable table — Name, Type, Capabilities (olive tags).
- **No issues**.

### Section: Classification (Overview tab)

- **Job to be done**: Track field classification progress across datasets.
- **Description**: Explains approved/classified/unlabeled status. Shows dynamic monitor count.
- **Layout**: Three columns — stepped progress bar with dot legend (left), monitors with status tags (center), categories with field counts and approval % (right).
- **Progress bar**: Green (approved) / Blue (classified) / Gray (unlabeled).
- **No issues**.

### Tab: Datasets

- **Job to be done**: View and manage datasets linked to this system.
- **Table/Graph toggle**: Segmented control switches between table view and React Flow graph view.
- **Table**: Searchable. Columns: Dataset, Data Categories (corinth tags), DSR Scope (olive tags), Fields, Collections, Actions (View + YAML).
- **Graph**: React Flow node diagram showing dataset → collection → field → category hierarchy.
- **Add**: Dataset picker modal — searchable list of datasets from other systems with name, system, field count. Multi-select.
- **No issues**.

### Tab: History

- **Job to be done**: GRC audit trail — who did what, when, with classification-level detail.
- **Filters**: Search bar (left), Category multi-select + User multi-select (right-aligned). Entry count.
- **Table**: Date, Category (sandstone/nectar/olive/minos tags), Action, User (avatar), Field, Change (old → new with strikethrough), Reason.
- **Category colors**: classification=sandstone, steward=nectar, integration=olive, purpose=minos, system=default.
- **Scrollable**: 700px max height with sticky header.
- **No issues**.

### Tab: Assets

- **Job to be done**: Manage cookies, pixels, tags, iframes, browser requests.
- **Table**: Searchable + type filter. Columns: Name, Type (colored tag), Domain, Categories of Consent (tags), Duration (cookies only), Detected On, Actions (Edit + Delete).
- **Add**: Modal with Name, Type, Domain, Data Uses, Description, Duration (cookies), Base URL (non-cookies).
- **Type tag colors**: Cookie=sandstone, Browser Request=olive, iFrame=nectar, Javascript tag=minos, Image=default.
- **No issues**.

### Tab: Advanced

- **Job to be done**: Configure advanced system properties not shown in Overview.
- **Layout**: Max-width 900px. Bordered section cards with neutral-75 headers. Two-column grid for short fields, full-width for textareas/multi-selects.
- **Sections**: Data Processing (9 fields), Cookie Properties (4 fields), Administrative (7 fields), Tags & Custom Fields (2 fields).
- **No issues**: Clean, scannable, no hidden accordions.

---

## Pillar Aggregation Audit

### The Four Pillars

| Pillar         | Root (computeGovernanceDimensions)                      | Detail (computeSystemDimensions)           |
| -------------- | ------------------------------------------------------- | ------------------------------------------ |
| **Annotation** | `avg(systems.annotation_percent)` — HARDCODED TO 58     | `system.annotation_percent` (real)         |
| **Compliance** | `(1 - totalIssues / maxIssues) * 100` — HARDCODED TO 92 | `(1 - issue_count / 5) * 100` (real)       |
| **Purpose**    | `systems_with_purposes / total * 100` — HARDCODED TO 84 | Binary: 100 if purposes exist, 0 otherwise |
| **Ownership**  | `systems_with_stewards / total * 100` — HARDCODED TO 66 | Binary: 100 if stewards exist, 0 otherwise |

### Does it aggregate logically to 0-100?

**Mathematically yes**: Each pillar is 0-100, the score is their average = 0-100.

**Semantic issues**:

1. **Root hardcoding**: `computeGovernanceDimensions` ignores computed values. Dead code.
2. **Binary detail pillars**: Purpose and Ownership are 0 or 100 on the detail page — no granularity.
3. **Classification not in pillars**: Classification approval rate is displayed but not factored into any pillar.
4. **DSR health not in pillars**: Privacy request processing health is not reflected in the governance score.

### Stacked Area Chart (RESOLVED)

- Data model now uses `score/4` per pillar, stacking to the overall score.
- March values match the donut: 14.5 + 23 + 21 + 16.5 = 75.
- Y-axis 0-100 is honest.

### Remaining Recommendations

1. **Fix `computeGovernanceDimensions`**: Remove hardcoded return, use computed values.
2. **Remove dead code**: Delete unused `annotationTrend`, `stewardTrend`, `purposeTrend` from `GovernanceHealthData`.
3. **Add pillar granularity**: Purpose could be `purposes.length / TARGET * 100`. Ownership could factor steward count + dataset coverage.
4. **Fold classification into Annotation pillar**: `(annotation_percent + classification_approval_pct) / 2`.
5. **Fold DSR health into Compliance pillar**: `issueHealth * 0.5 + dsrHealth * 0.5`.
