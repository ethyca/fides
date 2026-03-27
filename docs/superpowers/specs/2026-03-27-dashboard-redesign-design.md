# Dashboard Redesign: Editorial Layout with 4-Tier Hierarchy

**Date:** 2026-03-27
**Mockup:** `docs/dashboard-mockups/variant-d-final-polish.html` (on branch `dashboard-design-1d`)
**Scope:** Restructure `HomeDashboard.tsx` layout and child component styles. No backend changes. No new API endpoints. All existing data hooks and FidesUI chart components remain.

## Design Principles

- **Typography and whitespace create hierarchy** — not cards. Cards used only where they group self-contained data units (TrendCards).
- **4-tier visual hierarchy**: Hero (GPS) → Actions → Dimensions/Trends → Supporting (Coverage + DSR).
- **Astralis annotations throughout** — each section gets AI context via limestone-bg Alert overrides.
- **Brand fonts**: Basier Square (body), Basier Square Mono (labels, values), per the existing Ant theme tokens.
- **Same data, same hooks** — layout changes only. All RTK Query hooks, data types, and FidesUI chart components stay.

## Architecture: What Changes vs What Stays

### Stays the same
- `HomeContainer.tsx` — no changes
- `CommandBar.tsx` — no changes
- `DashboardDrawer.tsx` — no changes
- All RTK Query hooks (`useGetDashboardPostureQuery`, `useGetDashboardTrendsQuery`, `useGetPriorityActionsQuery`, `useGetPrivacyRequestsQuery`, `useGetSystemCoverageQuery`, `useGetAgentBriefingQuery`)
- All FidesUI chart components (`RadarChart`, `Sparkline`, `DonutChart`, `StackedBarChart`, `Statistic`, `Tag`)
- All data types in `~/features/dashboard/types.ts`

### Changes

| File | Change |
|------|--------|
| `HomeDashboard.tsx` | Replace `Row`/`Col` grid with 4-tier vertical layout using Tailwind CSS grid |
| `PostureCard.tsx` | Extract from `Card` wrapper. Split into left (score + narrative) and right (radar). Push `Statistic` to 96px hero size |
| `AgentBriefingBanner.tsx` | Restyle and reposition under posture hero section. Limestone bg Alert style |
| `PriorityActionsCard.tsx` | Remove `Card` wrapper. Full-width list. Cap visible items. Add expand button. Text-link CTAs |
| `TrendCard.tsx` | Keep `Card variant="borderless"` with `coverPosition="bottom"`. Add Astralis annotation between stat and sparkline |
| `SystemCoverageCard.tsx` | Remove `Card` wrapper. Narrow column layout (320px). Center donut vertically |
| `DSRStatusCard.tsx` | Remove `Card` wrapper. Wide column. Stat blocks row instead of inline text. SLA chart stays as `StackedBarChart` |
| New: `HomeDashboard.module.scss` | Layout styles for the 4-tier structure |
| New: `PostureHero.module.scss` | Hero section styles (96px score, split grid) |
| New: `PriorityActions.module.scss` | Left-border accents, expand button styles |

## Implementation Plan

### Step 1: HomeDashboard.tsx — Layout Restructure

Replace the current `Row`/`Col` layout with a vertical flex container holding 4 distinct tiers:

```tsx
// Current
<Flex vertical gap={24} className="mx-auto w-full max-w-[1600px] px-10 py-6">
  <AgentBriefingBanner />
  <Row gutter={24}> ... PostureCard + PriorityActionsCard </Row>
  <Row gutter={24}> ... TrendCards </Row>
  <Row gutter={24}> ... SystemCoverage + DSRStatus </Row>
  <DashboardDrawer />
</Flex>

// New
<Flex vertical className="mx-auto w-full max-w-[1600px] px-10">
  {/* Tier 1: Hero — GPS + Radar */}
  <PostureHero />

  {/* Tier 2: Priority Actions — full width, capped */}
  <PriorityActionsSection />

  {/* Tier 3: Dimension Trend Cards — 4-col grid with gaps */}
  <div className="grid grid-cols-4 gap-4 border-b border-neutral-100 py-8">
    {TREND_METRIC_KEYS.map((key) => (
      <TrendCard key={key} metricKey={key} metric={metrics?.[key]} isLoading={isTrendsLoading} />
    ))}
  </div>

  {/* Tier 4: Coverage (narrow) + DSR (wide) */}
  <div className="grid grid-cols-[320px_1fr] py-10">
    <SystemCoverageSection />
    <DSRStatusSection />
  </div>

  <DashboardDrawer />
</Flex>
```

Remove `AgentBriefingBanner` from the top level — its content moves into `PostureHero`.

### Step 2: PostureHero — New Component (replaces PostureCard + AgentBriefingBanner)

Create `PostureHero.tsx` that combines the GPS score, radar chart, and Astralis briefing into one hero section.

**Layout:** `grid grid-cols-2 gap-12 border-b border-neutral-100 py-14`

**Left column:**
- Section label: `<Text>` with `fontFamily: fontFamilyCode`, uppercase, `color: colorTextDisabled`, `letterSpacing: 2px`
- GPS score: `<Statistic value={animatedScore} valueStyle={{ fontSize: 96, fontWeight: 200, letterSpacing: -3 }} />` — clickable, opens posture drawer
- Trend: `<Tag color="success">` pill with `↑ 4 pts` + secondary text "from last week"
- Narrative: `<Text type="secondary">` with 15px font size, max-width 440px
- Astralis card: `<Alert type="info" showIcon icon={<SparkleIcon />} className={styles.astralisCard}>` — override: limestone bg, no border. Content combines the agent briefing text + action links from `useGetAgentBriefingQuery`

**Right column:**
- `<RadarChart>` at full size (outerRadius="80%"), centered
- Hint text below: "Click a dimension to explore breakdown"
- `onDimensionClick` opens the posture drawer (not filter actions)

**Data hooks used:** `useGetDashboardPostureQuery`, `useGetAgentBriefingQuery`, `useCountUp`

### Step 3: PriorityActionsSection — Restyle PriorityActionsCard

Modify `PriorityActionsCard.tsx` to remove the `Card` wrapper and adopt the new layout:

**Header:** `<Flex>` with section label + `<Segmented>` for tabs (Act now / Scheduled / When ready) with count badges

**List items:** Keep `<List>` but override styles via new SCSS module:
- Remove Card wrapper entirely — render List directly
- Each `<List.Item>` gets a left border accent via CSS class based on severity:
  - Critical: `border-left: 3px solid var(--fidesui-error)`
  - High: `border-left: 3px solid var(--fidesui-warning)`
  - Medium: `border-left: 3px solid var(--fidesui-olive)`
- Title stays as `<List.Item.Meta title={action.title} description={action.message} />`
- Due date: styled mono text with urgency color (overdue = error, approaching = warning)
- CTA: Replace `<Button>` with `<Typography.Link>` — text link with arrow: "View request →"

**Capped list:** Show max ~3-5 items per tab. Below the list, render an expand `<Button>` centered: "Show all actions (7)" that expands the section to show all items (no page navigation).

**Empty state:** Keep the existing "All clear" empty state.

### Step 4: TrendCard — Add Astralis Annotation

Modify `TrendCard.tsx` minimally:

- Keep `<Card variant="borderless" coverPosition="bottom" cover={<Sparkline />}>` — this already works exactly as the mockup shows
- Add an Astralis one-liner between the `<Statistic>` and the sparkline cover:
  - `<SparkleIcon size={10} />` + short text from posture dimension data
  - Font: 11px, `color: colorTextTertiary`
  - This requires passing dimension annotation data as a prop (from posture query, matched by metric key)

### Step 5: SystemCoverageSection — Narrow Column Restyle

Modify `SystemCoverageCard.tsx`:

- Remove `Card` wrapper
- Add right border: `border-r border-neutral-100 pr-10`
- Center the donut chart vertically with headline text below it
- Keep `<DonutChart variant="thick">` and breakdown list as-is
- Add Astralis card at the bottom: limestone `<Alert>` with GPS improvement suggestion

### Step 6: DSRStatusSection — Wide Column Restyle

Modify `DSRStatusCard.tsx`:

- Remove `Card` wrapper
- Add left padding: `pl-10`
- **Hero stat row:** Large `<Statistic value={18} valueStyle={{ fontSize: 48, fontWeight: 200 }} />` on left, then 4 secondary stats (`In Progress`, `Pending Action`, `Awaiting Approval`, `Overdue`) as individual `<Statistic>` blocks spread horizontally. Separated from rest by bottom border.
- **SLA Health:** Keep `<StackedBarChart>` as-is — it already renders one bar per DSR type with clickable labels. The component handles this correctly.
- Add Astralis card at the bottom

### Step 7: New SCSS Modules

**`HomeDashboard.module.scss`:**
- Tier separators: `border-bottom: 1px solid var(--fidesui-neutral-100)`
- Tier padding: progressively decreasing (56px hero → 36px actions → 32px trends → 40px supporting)

**`PostureHero.module.scss`:**
- Hero score override: push Statistic to 96px
- Astralis card: limestone bg, no border, 8px radius
- Radar container sizing

**`PriorityActions.module.scss`:**
- Left border accent per severity
- Expand button centered styling
- Due text mono styling
- CTA link terracotta color

## What This Does NOT Change

- No new API endpoints
- No changes to data types or RTK Query slices
- No changes to FidesUI component library (all customization via className/valueStyle overrides)
- No changes to routing, auth, or feature flags
- CommandBar stays as-is
- DashboardDrawer stays as-is
- Dark mode support maintained (Ant token-based colors adapt automatically)

## Component Mapping Summary

| Mockup Element | Ant/FidesUI Component | Customization |
|---|---|---|
| GPS "78" | `<Statistic>` | `valueStyle={{ fontSize: 96, fontWeight: 200 }}` |
| Trend pill "+4 pts" | `<Tag color="success">` | Pill border-radius via className |
| Radar chart | `<RadarChart>` | `outerRadius="80%"`, larger container |
| Astralis cards | `<Alert type="info">` | className override: limestone bg, no border |
| Section labels | `<Text>` | `fontFamily: fontFamilyCode`, uppercase |
| Action tabs | `<Segmented>` | With count badges |
| Action list | `<List>` | Custom SCSS for left-border accents |
| Action CTA | `<Typography.Link>` | Terracotta color + arrow |
| Expand button | `<Button>` | Centered, default variant |
| Trend cards | `<Card variant="borderless">` | `coverPosition="bottom"`, keep as-is |
| Sparklines | `<Sparkline>` | No changes |
| Donut chart | `<DonutChart variant="thick">` | No changes |
| SLA bars | `<StackedBarChart>` | No changes |
| DSR stats | `<Statistic>` | Various sizes via `valueStyle` |
| Severity dots | CSS `border-left` | 3px colored accent |
| Due text | `<Text>` | `fontFamily: fontFamilyCode`, colored by urgency |

## Estimated Scope

- **HomeDashboard.tsx**: Small — layout restructure only
- **PostureHero.tsx**: Medium — new component combining PostureCard + AgentBriefingBanner logic
- **PriorityActionsCard.tsx**: Medium — remove Card, restyle list items, add expand
- **TrendCard.tsx**: Small — add annotation prop
- **SystemCoverageCard.tsx**: Small — remove Card, adjust layout
- **DSRStatusCard.tsx**: Medium — remove Card, restructure stat display
- **SCSS modules**: Small — mostly Tailwind with a few custom overrides
