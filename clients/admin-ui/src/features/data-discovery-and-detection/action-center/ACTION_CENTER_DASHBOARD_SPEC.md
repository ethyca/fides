# Action Center Dashboard — Engineering Spec

## Overview

The Action Center Dashboard displays a row of summary widgets at the top of `/data-discovery/action-center`. Each widget represents a monitor type (Infrastructure, Data Stores, Web Monitors) and shows aggregate stats, a completion rate, status breakdown, and category/use tags.

The design has three states: **full data**, **no action required** (low data), and **empty** (no monitors configured).

---

## Files

| File | Role |
|------|------|
| `ActionCenterDashboard.tsx` | Orchestrator — receives monitors, groups by type, renders cards |
| `MonitorSummaryCard.tsx` | The card widget — two layouts: `stat-grid` (infrastructure) and `sparkline` (datastore/web) |
| `dashboardFakeData.ts` | Placeholder data for categories/uses — **replace with API data** |
| `types.d.ts` | `MonitorAggregatedResults` interface |
| `action-center.slice.ts` | RTK Query endpoint `getAggregateMonitorResults` (already exists) |

---

## What's hardcoded (needs real data)

### 1. `MONITOR_TYPE_CONFIG.overall` — Completion rate numerator/denominator

Currently hardcoded per type in `MonitorSummaryCard.tsx`:

```ts
overall: { totalDiscovered: 52_853, approved: 34_000 }  // datastore
overall: { totalDiscovered: 2_327, approved: 680 }       // web
overall: { totalDiscovered: 154, approved: 142 }          // infra
```

**What the UI needs:**
- `totalDiscovered`: Total number of resources discovered across all monitors of this type
- `approved`: Number of resources that have been approved/promoted

**Displayed as:**
- Circle progress: `Math.round((approved / totalDiscovered) * 100)`%
- Text below circle: `"{approved} of {totalDiscovered}"`
- Stat grid (infra): "Total systems", "Approved", "Need attention" (`totalDiscovered - approved`), "Coverage" (`percent`)

**Suggested endpoint shape:**

```json
GET /plus/discovery-monitor/dashboard-summary

{
  "datastore": {
    "total_discovered": 52853,
    "approved": 34000,
    "monitor_count": 3
  },
  "website": {
    "total_discovered": 2327,
    "approved": 680,
    "monitor_count": 2
  },
  "infrastructure": {
    "total_discovered": 154,
    "approved": 142,
    "monitor_count": 1
  }
}
```

Alternatively, this could be computed client-side from the existing `getAggregateMonitorResults` response if we add `total_discovered` and `approved` fields to `MonitorConfigStagedResourcesAggregateRecord`.

---

### 2. `MONITOR_TYPE_CONFIG.timeSeries` — Sparkline chart data

Currently hardcoded monthly data points in `MonitorSummaryCard.tsx`:

```ts
timeSeries: [
  { label: "Oct", value: 1_820 },
  { label: "Nov", value: 2_140 },
  // ...
]
```

**What the UI needs:**
- An array of `{ label: string, value: number }` representing resources detected over time (last 6 months)
- Used to render the sparkline area chart (datastore and web cards only; infrastructure uses stat-grid layout, no sparkline)
- The delta between the last two points is displayed as `"+X% vs last mo"`

**Suggested endpoint shape:**

```json
GET /plus/discovery-monitor/dashboard-summary/time-series?monitor_type=datastore&period=monthly&count=6

{
  "points": [
    { "label": "Oct", "value": 1820 },
    { "label": "Nov", "value": 2140 },
    { "label": "Dec", "value": 2580 },
    { "label": "Jan", "value": 3010 },
    { "label": "Feb", "value": 3490 },
    { "label": "Mar", "value": 3853 }
  ]
}
```

Could also be a field on the dashboard summary response instead of a separate call.

---

### 3. `tagSection.data` — Category/use tags

Currently sourced from `dashboardFakeData.ts`:

```ts
FAKE_DATA_CATEGORIES = [
  { label: "Email address", value: 612 },
  { label: "Name", value: 487 },
  // ...
]

FAKE_DATA_USES = [
  { label: "Marketing", value: 423 },
  // ...
]
```

**What the UI needs per type:**

| Type | Section title | Data |
|------|---------------|------|
| Datastore | DATA CATEGORIES | Top data categories detected, with counts |
| Web | CATEGORIES OF CONSENT | Top consent categories, with counts |
| Infrastructure | DATA USES | Top data uses, with counts |

Each item is rendered as a tag pill: `"{label} {percent}%"` where percent = `Math.round((value / total) * 100)`.

**Suggested endpoint shape:**

```json
GET /plus/discovery-monitor/dashboard-summary/tags?monitor_type=datastore

{
  "title": "DATA CATEGORIES",
  "items": [
    { "label": "Email address", "value": 612 },
    { "label": "Name", "value": 487 },
    { "label": "Phone number", "value": 234 }
  ]
}
```

---

### 4. Breakdown items — "CURRENT STATUS" section

This data is **already derived from the existing API**. The `getBreakdownItems()` function in `MonitorSummaryCard.tsx` aggregates the `updates` field across all monitors of a type:

| Type | Fields summed from `updates` | Displayed labels |
|------|------------------------------|------------------|
| Datastore | `unlabeled`, `classifying`, `in_review`, `reviewed` | unlabeled · classifying · classified · reviewed |
| Web | `cookie`, `javascript_tag`, `image`, `iframe`, `browser_request` | cookies · tags · pixels · iframes · requests |
| Infrastructure | Computed as 90% known / 10% unknown from `total_updates` | known · unknown |

**Note:** The infrastructure known/unknown split is a placeholder (`Math.round(total * 0.9)`). This needs a real data source — either new fields on `InfrastructureMonitorUpdates` or a separate computation.

---

## What already works (from existing API)

The `getAggregateMonitorResults` endpoint at `/plus/discovery-monitor/aggregate-results` returns the per-monitor data used for:

- **Monitor count**: `monitors.length` per type
- **`updates` breakdown**: Summed across monitors for the "CURRENT STATUS" section
- **`total_updates`**: Used for the low-data threshold check
- **`connection_type`**: Used to determine `MONITOR_TYPES` via `getMonitorType()`
- **`last_monitored`**: Available but not currently displayed in the dashboard
- **`has_failed_tasks`**: Available but not currently displayed

The response shape per monitor:

```ts
{
  name: string;
  key: string;
  connection_type: ConnectionType;
  last_monitored: string | null;
  total_updates: number;
  updates: DatastoreMonitorUpdates | WebMonitorUpdates | InfrastructureMonitorUpdates;
  has_failed_tasks: boolean | null;
  stewards: MonitorStewardUserResponse[];
}
```

---

## Card states

### Full data
All sections visible: header, hero (stat grid or sparkline), breakdown, tags. No special handling needed — the default render path.

### No action required (`isLowData`)
Triggered when `sum(total_updates) < 50` across all monitors of a type. When active:
- Circle progress shows **100%** (green)
- `approved` and `total` both set to the actual `monitorUpdatesTotal`
- Breakdown and tags sections **hidden**
- Shows a green checkmark + "No action required" message

This is a **client-side heuristic** for now. If the backend can provide a "needs attention" boolean or count, that would be better.

### Empty (no monitors)
Triggered when `monitors.length === 0` for a type. Shows:
- Type title only (no monitor count)
- A centered icon + description text prompting the user to set up a monitor

---

## Wiring it up

### Step 1: Create the dashboard summary endpoint

New endpoint that returns aggregate totals per monitor type. This powers the completion rate circle and the stat grid.

```
GET /plus/discovery-monitor/dashboard-summary
```

Response should include `total_discovered`, `approved`, and `monitor_count` per type.

### Step 2: Add time series endpoint (or field)

Powers the sparkline charts. Needs monthly (or configurable period) resource detection counts per monitor type for the last N months.

### Step 3: Add tag distribution endpoint (or field)

Powers the category/use tag pills. Needs top-N items with counts per monitor type.

### Step 4: Replace hardcoded config in `MonitorSummaryCard.tsx`

The `MONITOR_TYPE_CONFIG` object has the hardcoded values. Replace:
- `overall` → from dashboard summary API
- `timeSeries` → from time series API
- `tagSection.data` → from tag distribution API
- Static fields (`title`, `rateLabel`, `unit`, etc.) stay as-is

### Step 5: Replace `FAKE_MONITORS` in `ActionCenterDashboard.tsx`

The dashboard currently ignores the `monitors` prop and uses `FAKE_MONITORS`. Change to:

```ts
const data = monitors; // prop from getAggregateMonitorResults
```

Remove `FAKE_MONITORS`, `LOW_DATA_MONITORS`, and the stacked debug rows (`FULL DATA` / `NO ACTION REQUIRED` / `EMPTY STATE`).

### Step 6: Clean up `dashboardFakeData.ts`

Once tags come from the API, this file can be deleted entirely.

---

## Existing types reference

```ts
// types/api/models/DatastoreMonitorUpdates.ts
type DatastoreMonitorUpdates = {
  unlabeled: number;
  in_review: number;
  classifying: number;
  removals: number;
  reviewed: number;
  classified_low_confidence: number | null;
  classified_medium_confidence: number | null;
  classified_high_confidence: number | null;
};

// types/api/models/WebMonitorUpdates.ts
type WebMonitorUpdates = {
  cookie?: number;
  browser_request?: number;
  image?: number;
  iframe?: number;
  javascript_tag?: number;
};

// types/api/models/InfrastructureMonitorUpdates.ts
type InfrastructureMonitorUpdates = {
  okta_app?: number;
};
```

---

## Color thresholds

The completion rate circle uses color to indicate health:

| Condition | Color | Hex |
|-----------|-------|-----|
| >= 75% | Green | `#5a9a68` |
| >= 40% | Amber | `#e59d47` |
| < 40% | Red | `#d9534f` |


