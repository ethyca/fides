# System Inventory — FE Review for Engineering

**TypeScript**: Clean (`tsc --noEmit` passes)
**ESLint**: Clean (0 errors, 0 warnings)
**Prettier**: Clean

---

## Completed (this branch)

### Lint — all passing

- Import sorting, Tailwind class ordering, Prettier formatting applied
- All `curly` / `nonblock-statement-body-position` fixed
- All `no-nested-ternary` extracted to helper functions
- All `no-plusplus` fixed
- All `aria-label` added to Select/Switch components
- All `jsx-a11y/click-events-have-key-events` fixed (clickable Text → Button)
- All `no-restricted-syntax` fixed (for...of → forEach)
- Array index keys replaced with stable keys
- Unused imports/vars removed
- `w-[25%]` replaced with `w-1/4` (Tailwind plugin)
- `recharts` and `@carbon/icons-react` added to admin-ui `package.json` dependencies
- Dead variant files deleted (`ChartVariants.tsx`, `DashboardVariants.tsx`)

### Code quality

- Hardcoded governance scores **fixed** — `computeGovernanceDimensions()` uses computed values
- `CapabilitiesSection` / `MiniMetric` removed from SystemDetailContent (moved to dashboard)
- Producer/consumer arrow icons removed from system cards
- No `React.FC` — all arrow function components
- No Ant `Table` — all flex row tables
- No Chakra imports — all fidesui

---

## P0 — Must fix before merge

### 1. Mock data → real API integration

**Files**: `mock-data.ts`, `hooks/useSystemInventory.ts`, `hooks/useSystemDetail.ts`
**Issue**: All data is hardcoded. Production requires RTK Query hooks.
**Fix**: Replace `MOCK_SYSTEMS` with `useGetSystemsQuery()`. Replace `useSystemDetail` with `useGetSystemByFidesKeyQuery()`. See [BACKEND_DEPENDENCIES.md](./BACKEND_DEPENDENCIES.md).

### 2. File extraction — SystemDetailContent.tsx (~1700 lines)

**Issue**: Single file with 20+ components.
**Fix**: Extract into separate files:

- `sections/AboutSection.tsx`
- `sections/GovernanceSection.tsx`
- `sections/IntegrationsSection.tsx`
- `sections/ClassificationSection.tsx`
- `tabs/HistoryContent.tsx`
- `tabs/AdvancedContent.tsx`

### 3. Dead files to delete

No longer imported or used:

- `detail/tabs/ConfigTab.tsx`
- `detail/tabs/OverviewTab.tsx`
- `detail/SystemDetailAlerts.tsx`
- `detail/SystemDetailStats.tsx`
- `components/SystemStatsRow.tsx`

---

## P1 — Nice to have

### 4. Test coverage

No tests for system-inventory components. Minimum: `computeGovernanceDimensions`, `computeSystemDimensions`, `getSystemCapabilities` unit tests + `SystemCard` render test.

### 5. Storybook stories

Add for `GovernanceScoreCard`, `SystemCard`, `HealthBadge`.

### 6. Feature flag

Consider `systemInventoryRevamp` flag to gate new pages.

### 7. Hardcoded hex colors

Some components use inline hex instead of palette tokens. Functional but less maintainable.

---

## Compliance summary

| Rule                 | Status                          |
| -------------------- | ------------------------------- |
| TypeScript strict    | **Pass**                        |
| ESLint               | **Pass** (0 errors, 0 warnings) |
| Prettier             | **Pass**                        |
| Import sorting       | **Pass**                        |
| Tailwind plugin      | **Pass**                        |
| React.FC ban         | **Pass**                        |
| Accessibility (aria) | **Pass**                        |
| No Ant Table         | **Pass**                        |
| No Chakra imports    | **Pass**                        |
| Test coverage        | Missing (P2)                    |
| Storybook            | Missing (P2)                    |
