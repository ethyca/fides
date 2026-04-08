# SidePanel + Icon Rail Navigation — Design Spec

**Date:** 2026-04-07
**Scope:** Build two new foundational components (IconRail, SidePanel) and integrate them into the existing layout. No page migrations, no IA restructuring, no route changes.

---

## 1. Architecture

Three-column layout replacing the current single-sidebar architecture:

```
┌──────────┬──────────────┬──────────────────────┐
│ IconRail │  SidePanel   │    Content Area       │
│  ~56px   │   ~220px     │    (flex: 1)          │
│          │  (optional)  │                       │
└──────────┴──────────────┴──────────────────────┘
```

- **IconRail** replaces `MainSideNav.tsx` entirely. Always visible, dark background.
- **SidePanel** is a new compound component. Wirable but empty in this step — pages compose it in a later step.
- **Content Area** unchanged — pages render here with their existing PageHeader, tabs, and filters.

---

## 2. Icon Rail

### 2.1 Location

```
clients/admin-ui/src/features/common/nav/IconRail/
├── index.ts              # Public exports
├── IconRail.tsx           # Main component (replaces MainSideNav)
├── IconRailItem.tsx       # Individual icon button with tooltip + hover highlight
├── ExpandedNav.tsx        # Full expanded nav content (all groups + sub-pages)
├── IconRail.module.scss   # Styles
└── IconRail.stories.tsx   # Storybook story
```

### 2.2 Collapsed State (~56px)

- Dark background (`palette.FIDESUI_MINOS`)
- Icons stacked vertically, centered horizontally
- Active group: accent background or left border indicator
- Fides logo at top links to Home (`/`)

**Rail items (top to bottom):**

| Position | Item | Icon Source | Behavior |
|----------|------|------------|----------|
| Top | Fides logo | `logoCollapsed` asset | Navigate to `/` |
| Middle | NAV_CONFIG groups | `group.icon` from config | See expand behavior |
| Separator | — | — | Visual divider |
| Bottom | Settings | `Icons.Settings` | Navigate to Settings |
| Bottom | Help | `Icons.Help` | Open docs.ethyca.com |
| Bottom | Account | `AccountDropdownMenu` | User menu + logout |

No collapse toggle — the rail is always 56px in its resting state.

### 2.3 Expanded State (~240px, on hover)

Triggered by `onMouseEnter` on the rail container. Dismissed by `onMouseLeave`.

- **Overlays** the SidePanel (does not push content) using `position: absolute` + `z-index`
- Width transition: `transition: width 0.2s ease` on the absolutely-positioned expanded panel (the rail's 56px footprint in the document flow does not change)
- Dark background matching the rail
- Shows ALL groups and their sub-pages in a single scrollable list

**Structure:**
- Each section header: icon + group name (uppercase, semibold)
- Sub-pages listed below each header, regular weight, using `NextLink`
- Active page highlighted globally with accent indicator
- Separator between nav groups and bottom utilities (Settings, Help, Account)

**Hover highlighting:** Moving cursor over a rail icon in expanded state highlights the corresponding section (background accent). Scroll-into-view if section is off-screen.

**Click behavior:**
- Section header (icon + name) → navigates to that group's first route
- Sub-page link → deep-links directly to that page
- All navigation uses `NextLink` for client-side routing

### 2.4 Implementation Details

**Data flow (unchanged):**
1. `useNav({ path: router.pathname })` returns `{ groups: NavGroup[], active: ActiveNav }`
2. `configureNavGroups()` applies scope, flag, Plus/OSS/Cloud filters
3. `findActiveNav()` determines active group and path
4. IconRail renders the filtered groups

**Container:** Plain `div` with fixed width (not Ant Sider — matching current MainSideNav pattern). Uses `VStack` (Chakra) for vertical stacking internally.

**Expanded content:** Ant `Menu` in `inline` mode via `NavMenu` wrapper, with `type: "group"` items for section headers. Reuses the existing `NavMenu` component and SCSS.

**Loading state:** While `plusQuery.isLoading`, render an empty 56px-wide dark div (same pattern as current MainSideNav).

**NavSearch:** The Cmd+K / Ctrl+K keyboard shortcut and `NavSearchModal` continue to work. The `NavSearch` component is mounted inside the IconRail — it renders only the keyboard listener and the spotlight-style modal. No inline search input in either collapsed or expanded rail state. The modal search covers the same use case without consuming rail space.

**Preserved integrations:**
- All `NAV_CONFIG` scope-based gating
- All feature flag checks (`requiresFlag`, `requiresAnyFlag`, `hidesIfFlag`)
- Plus/OSS/Cloud environment checks
- `hidden: true` route exclusion
- localStorage for open keys
- Account dropdown with logout flow
- Help button linking to docs.ethyca.com

### 2.5 Styles

SCSS module (`IconRail.module.scss`):

```scss
// Key style targets
.rail {
  position: relative; // Establishes positioning context for expanded overlay
  min-width: 56px;
  max-width: 56px;
  height: 100%;
  background-color: var(--fidesui-minos);
  z-index: 30; // Above SidePanel (z-index 10), below modals (z-index 40+)
  display: flex;
  flex-direction: column;
}

.expandedOverlay {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  width: 240px;
  background-color: var(--fidesui-minos);
  z-index: 30;
  overflow-y: auto;
  transition: opacity 0.15s ease;
}

.railIcon {
  // 56px square, centered icon, hover state
}

.railIconActive {
  // Accent background or left border
}

.sectionHeader {
  // Uppercase, semibold, group name
}

.sectionHighlighted {
  // Background accent when hovering corresponding icon
}
```

---

## 3. SidePanel

### 3.1 Location

```
clients/admin-ui/src/features/common/SidePanel/
├── index.ts                    # Public exports
├── SidePanel.tsx               # Container + auto-sort logic
├── SidePanelContext.tsx         # Shared context (collapsed state, responsive)
├── slots/
│   ├── Identity.tsx            # Page title, breadcrumb, description
│   ├── Navigation.tsx          # Within-page nav (tab/view switcher)
│   ├── Search.tsx              # Page-level search input
│   ├── Actions.tsx             # Primary/bulk/form actions
│   ├── Filters.tsx             # Stacked filters with count badge
│   ├── ViewSettings.tsx        # Column visibility, display toggles
│   └── SavedViews.tsx          # Named filter/view presets
├── hooks/
│   ├── useSidePanelCollapse.ts # Responsive collapse logic
│   └── useSidePanelSlots.ts    # Child sorting/ordering logic
├── SidePanel.module.scss       # Panel-specific styles
├── SidePanel.stories.tsx       # Storybook stories
└── __tests__/
    └── SidePanel.test.tsx
```

### 3.2 Compound Component Pattern

Each slot component has a static `slotOrder` property. The parent `SidePanel` reads `React.Children`, checks `child.type.slotOrder`, sorts, and renders in canonical order.

**Canonical slot order:**

| Order | Slot | Ant Components | Default State |
|-------|------|---------------|---------------|
| 0 | `SidePanel.Identity` | `Typography.Title` level 4, `Breadcrumb`, `Typography.Text` | Always visible |
| 1 | `SidePanel.Navigation` | `Menu` vertical/inline | Visible when provided |
| 2 | `SidePanel.Search` | `Input.Search` | Visible when provided |
| 3 | `SidePanel.Actions` | `Button`, `Badge` | Visible when provided |
| 4 | `SidePanel.Filters` | `Collapse`, `Badge`, filter controls | Open by default |
| 5 | `SidePanel.ViewSettings` | `Collapse`, `Checkbox.Group` | Collapsed by default |
| 6 | `SidePanel.SavedViews` | `Collapse` | Collapsed by default |

All Ant components imported from `fidesui`, never directly from `antd`.

### 3.3 Container

```tsx
const SidePanel: React.FC<{ children: React.ReactNode }> & {
  Identity: typeof Identity;
  Navigation: typeof Navigation;
  Search: typeof Search;
  Actions: typeof Actions;
  Filters: typeof Filters;
  ViewSettings: typeof ViewSettings;
  SavedViews: typeof SavedViews;
}
```

- Uses Ant `Layout.Sider` from `fidesui` at `width={PANEL_WIDTH}` (220px), `theme="light"`
- Light background (matches content area or slightly offset)
- Full height, vertically scrollable
- Internal padding via SCSS

### 3.4 Slot Interfaces

```tsx
// Identity
interface IdentityProps {
  title: string;
  breadcrumbItems?: Array<{ title: string; href?: string }>;
  description?: string;
}

// Navigation
interface NavigationProps {
  items: Array<{
    key: string;
    label: string;
    disabled?: boolean;
    hidden?: boolean;
    type?: "group";
    children?: Array<{ key: string; label: string; disabled?: boolean }>;
  }>;
  activeKey: string;
  onSelect: (key: string) => void;
}

// Search
interface SearchProps {
  placeholder?: string;
  onSearch: (value: string) => void;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  value?: string;
  loading?: boolean;
}

// Actions
interface ActionsProps {
  children: React.ReactNode;
}

// Filters
interface FiltersProps {
  activeCount?: number;
  onClearAll?: () => void;
  children: React.ReactNode;
  defaultOpen?: boolean; // defaults to true
}

// ViewSettings
interface ViewSettingsProps {
  children: React.ReactNode;
  defaultOpen?: boolean; // defaults to false
}

// SavedViews
interface SavedViewsProps {
  children: React.ReactNode;
  defaultOpen?: boolean; // defaults to false
}
```

### 3.5 Responsive Behavior

`useSidePanelCollapse` hook:

```tsx
interface SidePanelCollapseState {
  collapsed: boolean;
  toggleCollapsed: () => void;
  isOverlay: boolean; // true when < 992px and panel is shown
}
```

- >= 992px: panel renders as normal Sider alongside content
- < 992px: panel collapses to zero width; toggle button opens as Ant `Drawer` overlay
- Panel collapse state is independent of the rail
- Breakpoint: 992px (matches Ant Design `lg` breakpoint)

### 3.6 Styles

```scss
.panel {
  border-right: 1px solid var(--fidesui-neutral-200);
  overflow-y: auto;
  height: 100%;
}

.panelContent {
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.overlay {
  // Drawer overlay mode for < 992px
}

.identity { /* spacing for title/breadcrumb/description */ }
.slotDivider { /* subtle separator between slots */ }
```

### 3.7 Context

`SidePanelContext` provides:
- `collapsed` state
- `toggleCollapsed` function
- `isOverlay` boolean
- `panelWidth` number (220)

Consumed by `useSidePanelCollapse` and available to any component that needs to know panel state.

---

## 4. Layout Integration

### 4.1 `_app.tsx` Changes

Replace `MainSideNav` with `IconRail`. Add SidePanel context wrapper. The SidePanel itself is not rendered in `_app.tsx` — individual pages will compose it when ready (Prompt 2).

```tsx
// Before:
<Flex width="100%" height="100%" flex={1}>
  <MainSideNav />
  <Flex direction="column" flex={1} minWidth={0} overflow="hidden">
    <Component {...pageProps} />
  </Flex>
</Flex>

// After:
<SidePanelProvider>
  <Flex width="100%" height="100%" flex={1}>
    <IconRail />
    <Flex direction="column" flex={1} minWidth={0} overflow="hidden">
      <Component {...pageProps} />
    </Flex>
  </Flex>
</SidePanelProvider>
```

### 4.2 Layout.tsx / FixedLayout.tsx

No changes in this step. These components wrap page content and are unaffected by the nav swap. The SidePanel will be integrated into pages in Prompt 2, at which point Layout.tsx may need adjustments.

---

## 5. Storybook

### 5.1 Config Change

Update `clients/fidesui/.storybook/main.ts` stories glob:

```ts
stories: [
  "../src/**/*.stories.@(js|jsx|mjs|ts|tsx)",
  "../../admin-ui/src/**/*.stories.@(js|jsx|mjs|ts|tsx)",
],
```

### 5.2 IconRail Story

**File:** `clients/admin-ui/src/features/common/nav/IconRail/IconRail.stories.tsx`

One story rendering the full icon rail in a `100vh` container:
- Mock `NavGroup[]` data derived from real NAV_CONFIG structure
- Collapsed state by default
- Expand-on-hover interaction
- Active page highlighting (one page marked active)
- `action()` callbacks for navigation clicks (no real routing)

### 5.3 SidePanel Stories

**File:** `clients/admin-ui/src/features/common/SidePanel/SidePanel.stories.tsx`

Three stories:

1. **ListPage** — Identity ("Systems") + Search + Actions ("Add system" button + conditional bulk actions) + Filters (3 mock Select filters). Most common page type.

2. **DetailPage** — Identity (breadcrumb "Systems > Acme Corp") + Navigation (5 tab items: Info, Data Uses, Data Flow, Assets, History) + Actions (Save + Delete).

3. **SettingsPage** — Identity ("Settings") + Navigation (grouped: Platform sub-items, Governance sub-items using `type: "group"`).

Each story renders in a simulated layout container (56px rail placeholder + 220px panel + content placeholder). Mock data and `action()` callbacks throughout.

---

## 6. What's NOT Changing

- `NAV_CONFIG` structure in `nav-config.tsx` (no IA refactor)
- `configureNavGroups()`, `findActiveNav()`, `configureNavRoute()` functions
- `useNav()` hook in `hooks.ts`
- `NavSearch` Cmd+K functionality
- Individual page implementations (PageHeader, tabs, filters stay)
- Route definitions in `routes.ts`
- `Layout.tsx` / `FixedLayout.tsx` (no changes this step)

---

## 7. Testing Approach

- **Unit test** (`SidePanel.test.tsx`): Verify auto-sort renders slots in canonical order regardless of JSX order
- **Storybook visual testing**: All 4 stories render without errors
- **TypeScript compilation**: No new type errors
- **Manual verification**: Icon rail renders with all current nav groups, hover expands, click navigates, all gating (scopes, flags, Plus) preserved
