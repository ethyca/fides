# System Inventory — Visual Design Reference

## Color Palette

### Brand colors (from `fidesui/src/palette/palette.module.scss`)

| Token | Hex | Usage |
|-------|-----|-------|
| `FIDESUI_CORINTH` | `#fafafa` | System card backgrounds |
| `FIDESUI_NEUTRAL_75` | `#f5f5f5` | Metric card fills, form section headers |
| `FIDESUI_NEUTRAL_100` | `#e6e6e8` | Purpose tags, data category tags (non-taxonomy), donut unfilled segments |
| `FIDESUI_TERRACOTTA` | `#b9704b` | Annotation pillar, brand accent |
| `FIDESUI_SANDSTONE` | `#cecac2` | Compliance pillar |
| `FIDESUI_OLIVE` | `#999b83` | Purpose pillar, DSR scope tags |
| `FIDESUI_MINOS` | `#2b2e35` | Ownership pillar, primary text, "View →" links |
| `FIDESUI_BG_DEFAULT` | `#f5f5f5` | AI briefing banner background |
| `FIDESUI_SUCCESS` | `#5a9a68` | Healthy status, approved tags, progress bars |
| `FIDESUI_WARNING` | `#e59d47` | Issues (1-2), pending tags |
| `FIDESUI_ERROR` | `#d9534f` | Issues (3+), error tags, delete actions |
| `FIDESUI_INFO` | `#4a90e2` | Classified/pending in stepped progress bar |

### Tag color assignments

| Context | Color |
|---------|-------|
| Purpose tags (system cards) | `neutral-100` fill, no border |
| Purpose tags (detail page) | `neutral-100` fill, no border |
| Data category tags (taxonomy) | `corinth` — matches fides taxonomy tag style |
| DSR scope tags | `olive` |
| Capability tags | `neutral-100` fill with Carbon icon |
| Asset type: Cookie | `sandstone` |
| Asset type: Browser Request | `olive` |
| Asset type: iFrame | `nectar` |
| Asset type: Javascript tag | `minos` |
| Asset type: Image | `default` |
| History category: classification | `sandstone` |
| History category: steward | `nectar` |
| History category: integration | `olive` |
| History category: purpose | `minos` |
| Health: Healthy | `success` (green) |
| Health: Issues (1-2) | `warning` (orange) |
| Health: Issues (3+) | `error` (red) |

## Layout Rules

### No unnecessary card wrappers
Dashboard sections are separated by **subtle border lines** (`border-l border-solid border-[#f0f0f0]`), not wrapped in Card components. Cards are used only when content is a discrete, bounded unit (e.g., Purposes card, Stewards card, metric cards).

### Section headers
Use the assessment-style pattern:
```tsx
<Title level={4} className="!mb-0 !mt-0">{title}</Title>
<Divider className="!mb-4 !mt-2" />
```
Followed by a secondary text description explaining the section's purpose.

### Responsive flex over fixed grid
Prefer `Flex` with `flex-1` / `shrink-0` over `Col span={N}` for dashboard layouts. This eliminates dead white space and lets content dictate sizing.

### Spacing
- Between major sections in overview: `gap={40}`
- Between dashboard metric cards: `gap={12}`
- Between section header and content: `Divider className="!mb-4 !mt-2"`
- Row padding in tables: `py-2` to `py-2.5`
- Activity feed rows: `py-1.5`

## Typography

### Labels
- Section titles: `Title level={4}` (bold, ~18px)
- Card titles: `Text strong className="text-sm"` (bold, 14px)
- Table headers: `text-[10px] uppercase tracking-wider` (all-caps, spaced)
- Field labels: `text-xs` (12px, secondary color)
- Metric labels: `text-[10px] uppercase tracking-wider`

### Values
- Hero numbers: `Statistic` with `text-5xl font-semibold` (dashboard score) or `Title level={2}` (metric cards)
- Field values in About section: `Text strong className="text-sm"`
- Table cell text: `text-xs` (12px)
- Timestamps: `text-[10px]` secondary

## Component Patterns

### Tables (lightweight flex-based)
Don't use Ant `Table` component. Use flex rows:
```tsx
{/* Header */}
<Flex className="border-b border-solid border-[#f0f0f0] px-3 py-2" style={{ backgroundColor: palette.FIDESUI_CORINTH }}>
  <Text strong className="w-[X%] text-[10px] uppercase tracking-wider">Column</Text>
</Flex>
{/* Rows */}
<Flex className="border-b border-solid border-[#f5f5f5] px-3 py-2.5">
  <Text className="w-[X%] text-xs">Value</Text>
</Flex>
```

### Picker modals
For adding purposes, stewards, integrations, datasets — use a searchable table inside a Modal:
- Search bar at top
- Optional filter dropdowns
- Table with header row (neutral-75 bg)
- Click rows to select/deselect
- "Selected" tag appears on selected rows
- OK button shows count: "Add 2 purposes"
- Existing items filtered out

### Edit modals
For editing system details, integration config:
- Full modal (width 520-600px)
- Vertical flex layout with `gap={16}`
- Side-by-side fields where they pair naturally (Name + Type, Access + Capabilities)
- Divider between sections within the modal
- Disabled fields for non-editable properties

### Confirmation modals
For destructive actions (delete system, remove integration):
- Width 420px
- Warning text with bold entity name
- Danger-colored OK button

### Donut charts (governance score)
- Padded-angle pie chart with rounded corners (`paddingAngle={4}`, `cornerRadius={2-3}`)
- Each pillar gets 25% of the ring (value=100 per pillar)
- Filled portion = score, unfilled = neutral-100 (`#e6e6e8`)
- 100% pillars skip the gray segment entirely
- Score displayed as `Statistic` in the center
- 2x2 key grid with brand-colored dots to the right

### Stacked area charts
- Each pillar contributes `score/4` so they stack to the overall score
- Brand color gradient fills (opacity 0.7 → 0.2)
- Y-axis 0-100, month labels on X-axis
- No grid vertical lines, dashed horizontal grid

### Circular progress (annotation in cards)
- Stoplight thresholds: ≥75% green, 40-74% orange, <40% red
- `size={20-24}`, `strokeWidth={12-14}`
- Percentage text next to it: "78% annotated"

### Health badge thresholds
- 0 issues → green "Healthy"
- 1-2 issues → orange "Issues"
- 3+ issues → red "Issues"

## Form Layout (Advanced tab)

### Bordered section cards
```tsx
<div className="rounded-lg border border-solid border-[#f0f0f0]">
  <div className="rounded-t-lg px-5 py-3" style={{ backgroundColor: palette.FIDESUI_NEUTRAL_75 }}>
    <Text strong className="text-sm">{title}</Text>
  </div>
  <div className="grid grid-cols-2 gap-x-6 gap-y-4 px-5 py-4">
    {children}
  </div>
</div>
```

- Max-width 900px container
- Two-column grid for short fields (switches, single inputs)
- `col-span-2` for textareas, multi-selects, long URLs
- Labels above inputs, left-justified
- No accordions — all fields visible

## AI Briefing Banner

- Background: `FIDESUI_BG_DEFAULT` (#f5f5f5)
- SparkleIcon (fidesui) on the left
- Natural language summary generated from system state
- "Needs attention" section with error-colored tags + text button CTAs
- Dismissible (sessionStorage-persisted)

## Icons

- Use Carbon icons from `@carbon/icons-react` (exported via fidesui)
- Capability icons: DSARs=Locked, Monitoring=Activity, Consent=Policy, Integrations=SettingsCheck, Classification=DataBase
- Section icons: WarningAlt (needs attention), Checkmark (healthy), Edit (edit actions), TrashCan (delete)
- AI/Agent: SparkleIcon from fidesui (not Carbon)

## What NOT to do

- Don't use Ant `Table` component for lightweight lists — use flex rows
- Don't wrap dashboard panels in `Card` — use border dividers
- Don't use accordions/collapse for forms — show all fields flat
- Don't use `Col span` for dashboard layouts — use `Flex` with `flex-1`
- Don't use full-width inputs spanning the screen — constrain to max-width
- Don't use inline tiny inputs for editing — use modals with proper sizing
- Don't hardcode governance scores — compute from system data
