# System Inventory — FE Review for Engineering

TypeScript compiles clean. ESLint has **0 real errors** (7 remaining are `import/no-extraneous-dependencies` false positives from monorepo package resolution).

---

## Completed (this branch)

### Lint fixes applied
- Import sorting via `eslint --fix`
- Tailwind class ordering via `eslint --fix`
- Prettier formatting applied
- All `curly` / `nonblock-statement-body-position` fixed — single-line returns wrapped in braces
- All `no-nested-ternary` extracted to helper functions
- All `no-plusplus` fixed (`i += 1`)
- `aria-label` added to Select and Switch components
- Array index keys replaced with stable keys
- `for...of` loops replaced with `.forEach()`
- Clickable `<Text>` elements replaced with `<Button type="text">`
- Unused imports/vars removed throughout

### Code quality
- Hardcoded governance scores **fixed** — `computeGovernanceDimensions()` uses computed values
- Dead variant files deleted (`ChartVariants.tsx`, `DashboardVariants.tsx`)
- `CapabilitiesSection` and `MiniMetric` removed from SystemDetailContent (moved to dashboard)
- Producer/consumer arrow icons removed from system cards
- No `React.FC` usage — all arrow function components
- No Ant `Table` — all flex row tables
- No Chakra imports — all fidesui

---

## P0 — Must fix before merge

### 1. Mock data → real API integration
**Files**: `mock-data.ts`, `hooks/useSystemInventory.ts`, `hooks/useSystemDetail.ts`
**Issue**: All data is hardcoded. Production requires RTK Query hooks.
**Fix**: Replace `MOCK_SYSTEMS` with `useGetSystemsQuery()`. Replace `useSystemDetail` with `useGetSystemByFidesKeyQuery()`. See [BACKEND_DEPENDENCIES.md](./BACKEND_DEPENDENCIES.md).

### 2. File size — SystemDetailContent.tsx (~1700 lines)
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

## P1 — Should fix before merge

### 4. Monorepo dependency warnings
7 `import/no-extraneous-dependencies` errors for `recharts` and `@carbon/icons-react`. These are in the monorepo root `node_modules`, not `admin-ui/package.json`. False positives — suppress with eslint comment or add to admin-ui deps.

### 5. Hardcoded hex colors
Some components use inline hex (`#e6e6e8`, `#53575c`, `#5a9a68`) instead of palette tokens. Functional but not maintainable.

### 6. Tailwind arbitrary value warnings
5 warnings for `w-[25%]` that could be `w-1/4`. Non-blocking.

---

## P2 — Nice to have

### 7. Test coverage
No tests for system-inventory components. Minimum: `computeGovernanceDimensions`, `computeSystemDimensions`, `getSystemCapabilities` unit tests + `SystemCard` render test.

### 8. Storybook stories
No stories. Add for `GovernanceScoreCard`, `SystemCard`, `HealthBadge`.

### 9. Feature flag
Consider `systemInventoryRevamp` flag to gate new pages.

---

## Compliance summary

| Rule | Status |
|------|--------|
| TypeScript strict | **Pass** |
| ESLint (real errors) | **Pass** (0 errors) |
| Import sorting | **Pass** |
| Tailwind plugin | **Pass** (5 warnings) |
| React.FC ban | **Pass** |
| Prettier | **Pass** |
| No Ant Table | **Pass** |
| No Chakra imports | **Pass** |
| Accessibility (aria) | **Pass** |
| Test coverage | **Missing** |
| Storybook | **Missing** |
