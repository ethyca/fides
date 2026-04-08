# System Inventory — UI Audit

## Route Page: `/system-inventory`

### Section: Dashboard Widget (GovernanceHealthDashboard)

| Aspect | Detail |
|--------|--------|
| **Job to be done** | Show overall governance posture at a glance — score, pillar breakdown, trends, recent activity |
| **Data source** | `GovernanceHealthData` from `computeGovernanceHealth()` in `utils.ts` |
| **What's indicated** | 4-pillar donut (Annotation, Compliance, Purpose, Ownership) averaging to a 0-100 score, 6-month stacked area trend, activity feed |

#### Panel 1: Inventory Health (Donut + Key)
- **Score**: Average of 4 pillar percentages. Currently **hardcoded** at 58/92/84/66 = 75.
- **Donut**: Each pillar gets 25% of the ring. Filled portion = pillar score. Unfilled = gray.
- **Key**: 4 items with brand-colored dots and percentage values.

**CRITICAL ISSUE**: `computeGovernanceDimensions()` calculates real values from system data (`annotationScore`, `complianceScore`, `purposeScore`, `stewardScore`) but the return statement on line 62-67 of `utils.ts` **ignores all computed values** and returns hardcoded numbers. The function's computation logic is dead code.

#### Panel 2: Health Over Time (Stacked Area Chart)
- **Data**: `TREND_DATA` is hardcoded mock — 6 months of 4 series stacked.
- **Y-axis**: 0-100.
- **Series**: annotation, compliance, purpose, ownership — each represented as a raw contribution count (not percentage).

**CRITICAL ISSUE**: The stacked values represent arbitrary contribution counts (e.g. annotation=2 in Oct, 14 in Mar) that sum to ~10-68 over the 6 months. These are **not the same metric** as the donut pillars (which are 0-100 percentages). The chart suggests pillar scores are tiny and stacking to a total, but the donut shows them as independent 0-100 values. This is visually misleading.

**DEAD CODE**: `annotationTrend`, `stewardTrend`, `purposeTrend` arrays are computed in `computeGovernanceHealth()` (lines 120-122 of `utils.ts`) but **never consumed** by any component. The dashboard's `TREND_DATA` is a separate hardcoded constant.

#### Panel 3: Recent Activity
- **Data**: Hardcoded `ACTIVITY` array with message, time, color, steward.
- **No issues**: This is display-only mock data, correctly structured.

### Section: System Card Grid

| Aspect | Detail |
|--------|--------|
| **Job to be done** | Browse systems, identify which need attention, navigate to detail |
| **Data source** | `MOCK_SYSTEMS` filtered by `useSystemInventory` hook |
| **What's indicated** | Health status (green/orange/red dot), purpose tags, annotation progress, steward presence |

- Cards are split into "Needs attention" (issue_count > 0) and "Healthy" sections.
- Each card shows: logo, name, roles, health badge, purpose tags, circular annotation progress, steward avatars.
- **No issues**: Layout is clear and functional.

### Section: Filters

| Aspect | Detail |
|--------|--------|
| **Job to be done** | Narrow system list by health, type, group, purpose |
| **Options**: "Needs attention" / "Healthy" for health filter (previously had "Has violations" which was removed) |
| **No issues**: Filters work correctly with `useMemo` filtering in the hook.

---

## Detail Page: `/system-inventory/[id]`

### Section: System Header
- Shows logo, name, system_type, department, responsibility.
- **No issues**.

### Section: AI Briefing Banner
- **Job to be done**: Surface the most important thing a steward needs to know about this system.
- **Data**: `agentBriefing` (if set) or `buildRichBriefing()` auto-generated summary + `getIssues()` for action items.
- **Issues listed**: no steward, fields needing review, no purposes, DSAR not enabled, plus any `system.issues[]`.
- **No issues**: Well-structured with clear CTAs.

### Section: Metric Cards (SystemDetailDashboardV2)

| Card | Data Source | Calculation |
|------|-----------|-------------|
| Governance Score | `computeSystemDimensions(system)` | Average of 4 pillars. Uses **real computed values** (not hardcoded). |
| Classification | `system.classification.approved / total` | Percentage of approved fields. |
| Privacy Requests | `system.privacyRequests.open` | Open count + closed/avg stats. |
| Datasets | `system.datasets.length` | Count + field/collection totals. |

**MEDIUM ISSUE**: Classification %, Privacy Requests, and Datasets are displayed as separate cards but are **not reflected in the 4-pillar governance score**. The governance score only considers annotation %, issue count, purpose presence, and steward presence. A system could have 0% classification and still score 100 if it has good annotation, no issues, purposes, and a steward.

### Section: About
- **Job to be done**: Quick reference for system identity.
- **Data**: Direct fields from `MockSystem`.
- **No issues**: Clean 2-column grid with edit modal.

### Section: Governance (Purposes + Stewards + Capabilities)
- **Job to be done**: Show and manage the governance metadata.
- **Capabilities are read-only** ("Based on active integrations") — derived from `getSystemCapabilities()`.
- **No issues**.

### Section: Classification Progress
- **Job to be done**: Show field classification status and monitor health.
- **Data**: `system.classification` (approved/pending/unreviewed) + `system.monitors`.
- **Stepped bar**: Green (approved) / Blue (classified/pending) / Gray (unlabeled/unreviewed).
- **No issues**: Three-column layout with progress bar, monitors, categories.

### Section: Connections & Data Flow
- **Job to be done**: Show integrations and data relationships.
- **Data**: `system.integrations` + `system.relationships`.
- **No issues**: Table + card layout side by side.

### Section: Datasets
- **Job to be done**: View datasets, their categories, status, and YAML.
- **Potential concern**: "Usage" column overlaps conceptually with purposes. Should be scoped to DSR operations specifically.

### Section: History Tab
- **Job to be done**: GRC audit trail — who did what, when, with classification-level detail.
- **Data**: `system.history[]` with expanded fields (category, fieldName, oldValue, newValue, reason).
- **Filters**: Category + User multi-selects + search bar.
- **No issues**: Rich and filterable.

### Section: Advanced Tab
- **Job to be done**: Edit system properties not shown in Overview.
- **Current UX**: Accordion panels — fields hidden behind collapses.
- **Issue**: Users must click to reveal fields. Should be a flat, scannable form.

---

## Pillar Aggregation Audit

### The Four Pillars

| Pillar | Root (computeGovernanceDimensions) | Detail (computeSystemDimensions) |
|--------|-----|--------|
| **Annotation** | `avg(systems.annotation_percent)` — BUT HARDCODED TO 58 | `system.annotation_percent` (real) |
| **Compliance** | `(1 - totalIssues / maxIssues) * 100` — BUT HARDCODED TO 92 | `(1 - issue_count / 5) * 100` (real) |
| **Purpose** | `systems_with_purposes / total * 100` — BUT HARDCODED TO 84 | Binary: 100 if purposes exist, 0 otherwise |
| **Ownership** | `systems_with_stewards / total * 100` — BUT HARDCODED TO 66 | Binary: 100 if stewards exist, 0 otherwise |

### Does it aggregate logically to 0-100?

**Mathematically yes**: Each pillar is 0-100, the score is their average = 0-100.

**Semantically, issues**:
1. **Binary pillars on detail page**: Purpose and Ownership are 0 or 100 — no granularity. A system with 1 purpose scores the same as one with 10. A system with 1 steward scores the same as one with 5.
2. **Compliance max issues cap**: Hardcoded to 5 max issues per system. A system with 6+ issues would go negative without the `Math.max(0, ...)` floor.
3. **Root vs. detail divergence**: Root hardcodes prevent any comparison between the aggregate view and individual system views.

### Time Series Chart Issues

1. **Data mismatch**: Chart data (`TREND_DATA`) uses stacked contribution counts (2-22 range), not pillar percentages (0-100).
2. **Visual misleading**: Y-axis is 0-100 but stacked totals only reach ~68, making it look like governance is at 68% when the donut says 75%.
3. **No connection to computed pillars**: The chart should show the same 4 pillar scores over time, each as a 0-100 percentage, NOT stacked.

### Recommendations

1. **Fix `computeGovernanceDimensions`**: Remove hardcoded return, use the computed values.
2. **Fix trend chart data model**: Use 4 independent lines (not stacked areas) each showing a pillar's 0-100 score over time. Or if stacked, divide each pillar by 4 so they sum to the overall score.
3. **Remove dead code**: Delete unused `annotationTrend`, `stewardTrend`, `purposeTrend` from `GovernanceHealthData`.
4. **Add granularity to detail pillars**: Purpose could be `purposes.length / MAX_PURPOSES * 100`. Ownership could factor in steward count or coverage.
5. **Integrate classification into pillars**: The Annotation pillar could incorporate classification approval rate, not just `annotation_percent`.
