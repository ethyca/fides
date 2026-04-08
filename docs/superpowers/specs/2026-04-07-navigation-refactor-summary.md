# Fides Navigation Refactor — Implementation Summary

**Date:** 2026-04-07
**Branch:** `experiment-nav-sidebar-ia-restructure` (forked from `experiment-nav-sidebar`)
**Scope:** 89 files changed, 2128 insertions, 2220 deletions

---

## What Was Done

### Phase 1: SidePanel + IconRail + Layout (prior session)

Built two foundational components and integrated them into the layout.

**IconRail** (`features/common/nav/IconRail/`)
- 56px collapsed rail with icon-only view, dark background
- Expands to 240px on hover via absolute overlay (does not push content)
- `ExpandedNav` shows all groups/sub-pages with scroll-into-view on section highlight
- Loading placeholder while Plus health query resolves
- NavSearch (Cmd+K) mounted inside the rail
- Remembers last-visited page per pillar in localStorage

**SidePanel** (`features/common/SidePanel/`)
- Compound component with 7 slots: Identity, Navigation, Search, Actions, Filters, ViewSettings, SavedViews
- Auto-sorts children by `slotOrder` via `useSidePanelSlots`
- Redux-backed state (`sidepanel.slice`) for responsive collapse at 992px with Drawer overlay mode
- `SidePanelProvider` sets up resize listener

**Layout Integration**
- `_app.tsx`: replaced `MainSideNav` with `IconRail` + `SidePanelProvider`, changed inner Flex to `direction="row"`
- `Layout.tsx`: added `flex={1}`, changed `h="100vh"` to `height="100%"`
- `FixedLayout.tsx`: same treatment
- `store.ts`: added `sidePanelSlice`

**Storybook**
- `fidesui/.storybook/main.ts`: added admin-ui stories glob
- `IconRail.stories.tsx`: self-contained story with mock nav groups
- `SidePanel.stories.tsx`: ListPage, DetailPage, SettingsPage stories

---

### Phase 2: Page Migrations (~80 pages)

Every page that used `PageHeader`, horizontal `Tabs`, or `FilterModal` was migrated to the SidePanel pattern.

**Pattern applied to every page:**
```tsx
// Before:
<Layout title="Page Title">
  <PageHeader heading="Page Title" breadcrumbItems={[...]} rightContent={<Button />} />
  <Tabs items={tabs} activeKey={activeTab} onChange={onTabChange} />
  <Content />
</Layout>

// After:
<>
  <SidePanel>
    <SidePanel.Identity title="Page Title" breadcrumbItems={[...]} />
    <SidePanel.Navigation items={navItems} activeKey={activeTab} onSelect={onTabChange} />
    <SidePanel.Actions><Button /></SidePanel.Actions>
  </SidePanel>
  <Layout title="Page Title">
    {activeTabContent}
    <Content />
  </Layout>
</>
```

**Replacement table (what was replaced with what):**

| Old Pattern | New Pattern |
|---|---|
| `PageHeader` heading + breadcrumb | `SidePanel.Identity` title + breadcrumbItems |
| `PageHeader` rightContent (buttons) | `SidePanel.Actions` |
| `PageHeader` children (description) | `SidePanel.Identity` description prop |
| Horizontal `Tabs` / `useURLHashedTabs` | `SidePanel.Navigation` + render active content |
| Horizontal `Menu` (route-based tabs) | `SidePanel.Navigation` with route-based onSelect |
| `DebouncedSearchInput` | `SidePanel.Search` |
| `GlobalFilterV2` (in TableActionBar) | `SidePanel.Search` |
| Inline date pickers / faceted search | `SidePanel.Filters` |
| Action buttons in page header | `SidePanel.Actions` |

**Pages migrated by group:**

- **Systems:** list, detail (tabs → Navigation), add, manual, multiple, test-datasets
- **Privacy Requests:** request manager (tabs → Navigation), policies list, policy detail (tabs → Navigation), request detail, configure
- **Consent:** privacy notices list + detail + new, privacy experiences, vendors, consent report, add vendors
- **Data Discovery:** ActionCenterLayout (shared component, Menu → Navigation), data catalog + 5 sub-pages, access control
- **Data Inventory:** datasets list + detail + 3 sub-pages + new, datamap, data map report, asset report
- **Integrations:** list, detail (tabs → Navigation)
- **Notifications:** templates list + detail + add, digests list + detail + new, providers, chat providers
- **Properties:** list, detail, add
- **Settings:** about, organization, locations, regulations, domains, email templates, privacy requests, custom fields (list + detail + new), RBAC (list + detail + new), consent settings + detail
- **User Management:** list, EditUserForm, NewUserForm
- **AI Governance:** access policies (list + onboarding), data purposes (list + detail + new), data consumers (list + detail + new), privacy assessments (list + detail), AccessPolicyEditor
- **Other:** taxonomy (TaxonomyPageContent), pre-approval webhooks, StorageConfiguration

**What was NOT migrated (intentionally):**
- POC/sandbox pages (5 files, development-only)
- `FilterModal` deep inside feature components (ConsentManagementTable, DatamapReportTable, SettingsBar, AddMultipleSystems) — too tightly coupled to refactor safely
- `PrivacyRequestFiltersBar` inside PrivacyRequestsDashboard — internal to the component

---

### Phase 3: IA Restructure + Pillar Dashboards

**NAV_CONFIG rewritten** from 10 groups to 7 pillar-based groups:

| Old Group | Disposition |
|---|---|
| Overview | → Dashboard |
| Detection & Discovery | → merged into Discovery & Inventory |
| Data inventory | → merged into Discovery & Inventory |
| Privacy requests | → Privacy Requests (expanded) |
| Privacy assessments | → merged into AI Governance |
| Consent | → Consent (expanded) |
| Core configuration | → split across AI Governance, Integrations, Consent, Settings |
| Compliance | → merged into Settings |
| Settings | → Settings (reorganized) |

**New pillar groups:**

1. **Dashboard** — Home route
2. **Discovery & Inventory** (Helios) — Dashboard, Activity Log (renamed Action Center), Systems, Add Systems, Datasets, Data Catalog, Data Lineage, Data Map Report, Asset Report
3. **Consent** (Janus) — Dashboard, Consent Report, Vendors, Privacy Notices, Privacy Experiences, Properties, Domains, Domain Verification, Consent Settings
4. **Privacy Requests** (Lethe) — Dashboard, Request Manager, DSR Policies, Pre-approval Webhooks, Messaging Templates, Digests, Privacy Request Settings, Email Templates
5. **AI Governance** (Astralis) — Dashboard, Violation Log (renamed Access Control), Access Policies, Data Purposes, Data Consumers, Privacy Assessments
6. **Integrations** — Integration List, Email Providers, Chat Providers
7. **Settings** — Organization, Users, Role Management, Notifications, Custom Fields, Taxonomy, Locations, Regulations, About Fides

**Renamed pages:**
- "Action center" → "Activity Log"
- "Access control" → "Violation Log"
- "System inventory" → "Systems"
- "Manage datasets" → "Datasets"

**4 pillar dashboard stubs created:**
- `/discovery-inventory` — Helios
- `/consent/dashboard` — Janus
- `/privacy-requests/dashboard` — Lethe
- `/ai-governance` — Astralis

**Remembered-page-per-pillar:** IconRail persists last-visited page per pillar in localStorage. Clicking a pillar returns to where you left off (defaults to dashboard on first visit).

---

### Phase 4: Cleanup

- Deleted `MainSideNav.tsx` (319 lines, zero remaining imports)
- Updated stale comment referencing MainSideNav in nav-config.tsx
- Verified zero TypeScript errors across entire codebase

---

## Architecture After Refactor

```
┌──────────┬──────────────┬──────────────────────┐
│ IconRail │  SidePanel   │    Content Area       │
│  ~56px   │   ~220px     │    (flex: 1)          │
│          │  (optional)  │                       │
└──────────┴──────────────┴──────────────────────┘
```

- **IconRail** always visible, dark background, expands on hover to show full nav map
- **SidePanel** composed per-page with slots (Identity, Navigation, Search, Actions, Filters)
- **Content Area** renders page content (tables, forms, charts)
- **Dashboards** skip SidePanel, render full-width

---

## Files Changed

| Category | Count |
|---|---|
| New components (Phase 1) | ~16 files |
| Layout changes | 3 files (_app.tsx, Layout.tsx, FixedLayout.tsx) |
| Page migrations | ~75 files |
| Feature component migrations | 5 files |
| NAV_CONFIG restructure | 2 files (nav-config.tsx, routes.ts) |
| New dashboard pages | 4 files |
| Deleted | 1 file (MainSideNav.tsx) |
| Storybook config | 1 file |
| Store config | 1 file |
| **Total** | **89 files changed** |

---

## What's NOT Changed

- All route paths preserved (no URL changes, no redirects needed)
- All `scopes`, `requiresPlus`, `requiresFlag`, `requiresFidesCloud` access controls preserved
- All state management (RTK Query hooks, filter hooks, form state) preserved
- `useURLHashedTabs` still used (drives tab state from URL hash for SidePanel.Navigation)
- `FilterModal` still used inside 4 feature components (too coupled for safe migration)
- `PageHeader` still used by 5 POC/sandbox dev pages
- Table column sorting, inline row actions, pagination, form fields all stay in content area
- `NavSearch` Cmd+K functionality preserved

---

## Known Limitations / Future Work

1. **FilterModal extraction:** ConsentManagementTable, DatamapReportTable, SettingsBar, and AddMultipleSystems still use modal-based filters internally. These should be refactored to use SidePanel.Filters in a follow-up.

2. **NotificationTabs:** The notifications sub-pages still use a horizontal `NotificationTabs` menu in the content area for route-based navigation. This should be converted to SidePanel.Navigation with route-based onSelect.

3. **Dashboard content:** All 4 pillar dashboards are stubs. The plan called for extracting overview/summary content from existing pages (Action Center → Helios dashboard, Access Control summary → Astralis dashboard, Request Manager stats → Lethe dashboard). This extraction was deferred because the content couldn't be cleanly separated without page refactoring.

4. **Hub consolidation:** The plan called for consolidating Reports (Data Map + Asset), Consent Settings (Properties + Domains + TCF/GPP/Publisher), and Privacy Requests Configuration (Templates + Digests + Redaction + Dedup + Storage) into hub pages with SidePanel.Navigation for view switching. These hubs are partially represented in NAV_CONFIG but the actual view-switching implementation was deferred.

5. **PrivacyRequestFiltersBar:** Still renders as a horizontal filter bar inside `PrivacyRequestsDashboard`. Should be lifted to SidePanel.Filters at the page level.

6. **POC pages:** 5 development-only pages still use PageHeader. Low priority since they're not user-facing.
