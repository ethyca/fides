import { Divider, Flex, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

// --- Shared chart styling ---

const GRID = { strokeDasharray: "3 3", stroke: "#f0f0f0", vertical: false } as const;
const AXIS_TICK = { fontSize: 10, fill: "#93969a" } as const;
const TT_STYLE = { borderRadius: 6, border: "1px solid #f0f0f0", fontSize: 11 };

const ChartLabel = ({ label }: { label: string }) => (
  <Text strong className="mb-2 block text-[10px] uppercase tracking-wider" style={{ color: palette.FIDESUI_MINOS }}>
    {label}
  </Text>
);

// --- V0: Current (raw contribution counts, stacked) ---

const V0_DATA = [
  { month: "Oct", annotation: 2, compliance: 4, purpose: 3, ownership: 1 },
  { month: "Nov", annotation: 5, compliance: 3, purpose: 8, ownership: 2 },
  { month: "Dec", annotation: 4, compliance: 10, purpose: 6, ownership: 5 },
  { month: "Jan", annotation: 10, compliance: 8, purpose: 12, ownership: 7 },
  { month: "Feb", annotation: 8, compliance: 16, purpose: 10, ownership: 14 },
  { month: "Mar", annotation: 14, compliance: 22, purpose: 20, ownership: 12 },
];

// --- V1: Stacked pillar contributions (score/4, sums to overall) ---

const V1_DATA = [
  { month: "Oct", annotation: 5.5, compliance: 12, purpose: 8.75, ownership: 7.5 },
  { month: "Nov", annotation: 7.5, compliance: 13.75, purpose: 10.5, ownership: 9.5 },
  { month: "Dec", annotation: 9.5, compliance: 15.5, purpose: 13.75, ownership: 11.25 },
  { month: "Jan", annotation: 10.5, compliance: 17.5, purpose: 17, ownership: 13 },
  { month: "Feb", annotation: 12.5, compliance: 20.5, purpose: 19.5, ownership: 14.5 },
  { month: "Mar", annotation: 14.5, compliance: 23, purpose: 21, ownership: 16.5 },
];

// --- V2: System counts by health ---

const V2_DATA = [
  { month: "Oct", healthy: 6, issues: 23 },
  { month: "Nov", healthy: 9, issues: 20 },
  { month: "Dec", healthy: 11, issues: 18 },
  { month: "Jan", healthy: 14, issues: 15 },
  { month: "Feb", healthy: 17, issues: 12 },
  { month: "Mar", healthy: 20, issues: 9 },
];

// --- V3: Issue resolution (trending down) ---

const V3_DATA = [
  { month: "Oct", noSteward: 14, unreviewed: 18, noPurpose: 10, noIntegration: 8 },
  { month: "Nov", noSteward: 12, unreviewed: 15, noPurpose: 8, noIntegration: 7 },
  { month: "Dec", noSteward: 10, unreviewed: 12, noPurpose: 6, noIntegration: 6 },
  { month: "Jan", noSteward: 8, unreviewed: 10, noPurpose: 5, noIntegration: 5 },
  { month: "Feb", noSteward: 6, unreviewed: 7, noPurpose: 4, noIntegration: 3 },
  { month: "Mar", noSteward: 5, unreviewed: 5, noPurpose: 3, noIntegration: 2 },
];

// --- V4: Dual — score line + stacked area ---

const V4_DATA = [
  { month: "Oct", annotation: 5.5, compliance: 12, purpose: 8.75, ownership: 7.5, overall: 34 },
  { month: "Nov", annotation: 7.5, compliance: 13.75, purpose: 10.5, ownership: 9.5, overall: 41 },
  { month: "Dec", annotation: 9.5, compliance: 15.5, purpose: 13.75, ownership: 11.25, overall: 50 },
  { month: "Jan", annotation: 10.5, compliance: 17.5, purpose: 17, ownership: 13, overall: 58 },
  { month: "Feb", annotation: 12.5, compliance: 20.5, purpose: 19.5, ownership: 14.5, overall: 67 },
  { month: "Mar", annotation: 14.5, compliance: 23, purpose: 21, ownership: 16.5, overall: 75 },
];

const PILLARS = [
  { key: "annotation", name: "Annotation", color: palette.FIDESUI_TERRACOTTA },
  { key: "compliance", name: "Compliance", color: palette.FIDESUI_SANDSTONE },
  { key: "purpose", name: "Purpose", color: palette.FIDESUI_OLIVE },
  { key: "ownership", name: "Ownership", color: palette.FIDESUI_MINOS },
];

const makeGrads = (prefix: string) =>
  PILLARS.map((s) => (
    <linearGradient key={s.key} id={`${prefix}-${s.key}`} x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stopColor={s.color} stopOpacity={0.7} />
      <stop offset="100%" stopColor={s.color} stopOpacity={0.2} />
    </linearGradient>
  ));

const Legend = ({ items }: { items: { name: string; color: string }[] }) => (
  <Flex gap={10} className="mb-2">
    {items.map((s) => (
      <Flex key={s.name} align="center" gap={4}>
        <div className="size-[5px] shrink-0 rounded-full" style={{ backgroundColor: s.color }} />
        <Text className="text-[9px]" style={{ color: palette.FIDESUI_MINOS }}>{s.name}</Text>
      </Flex>
    ))}
  </Flex>
);

// ===== VARIANTS =====

const ChartVariants = () => (
  <Flex vertical gap={8}>
    {/* V0 */}
    <ChartLabel label="V0 — Current: Raw Contribution Counts (Stacked)" />
    <Text type="secondary" className="!-mt-1 mb-1 text-[10px]">Problem: values are arbitrary counts (2-22), not percentages. Y-axis 0-100 is misleading.</Text>
    <Legend items={PILLARS} />
    <div className="h-[140px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={V0_DATA} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
          <defs>{makeGrads("v0")}</defs>
          <CartesianGrid {...GRID} />
          <XAxis dataKey="month" axisLine={false} tickLine={false} tick={AXIS_TICK} />
          <YAxis domain={[0, 100]} axisLine={false} tickLine={false} tick={AXIS_TICK} />
          <Tooltip contentStyle={TT_STYLE} />
          {PILLARS.map((s) => <Area key={s.key} type="monotone" dataKey={s.key} name={s.name} stroke={s.color} strokeWidth={1} fill={`url(#v0-${s.key})`} stackId="s" dot={false} />)}
        </AreaChart>
      </ResponsiveContainer>
    </div>

    <Divider className="!my-3" />

    {/* V1 */}
    <ChartLabel label="V1 — Stacked Pillar Contributions (score/4, sums to overall)" />
    <Text type="secondary" className="!-mt-1 mb-1 text-[10px]">Each pillar contributes its score/4. Top edge = overall health score. Honest and beautiful.</Text>
    <Legend items={PILLARS} />
    <div className="h-[140px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={V1_DATA} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
          <defs>{makeGrads("v1")}</defs>
          <CartesianGrid {...GRID} />
          <XAxis dataKey="month" axisLine={false} tickLine={false} tick={AXIS_TICK} />
          <YAxis domain={[0, 100]} axisLine={false} tickLine={false} tick={AXIS_TICK} />
          <Tooltip contentStyle={TT_STYLE} />
          {PILLARS.map((s) => <Area key={s.key} type="monotone" dataKey={s.key} name={s.name} stroke={s.color} strokeWidth={1} fill={`url(#v1-${s.key})`} stackId="s" dot={false} />)}
        </AreaChart>
      </ResponsiveContainer>
    </div>

    <Divider className="!my-3" />

    {/* V2 */}
    <ChartLabel label="V2 — System Counts by Health (healthy growing, issues shrinking)" />
    <Text type="secondary" className="!-mt-1 mb-1 text-[10px]">Story: we&apos;re fixing systems. Green grows, orange shrinks.</Text>
    <Legend items={[{ name: "Healthy", color: palette.FIDESUI_SUCCESS }, { name: "Has Issues", color: palette.FIDESUI_WARNING }]} />
    <div className="h-[140px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={V2_DATA} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
          <defs>
            <linearGradient id="v2-healthy" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={palette.FIDESUI_SUCCESS} stopOpacity={0.6} /><stop offset="100%" stopColor={palette.FIDESUI_SUCCESS} stopOpacity={0.15} /></linearGradient>
            <linearGradient id="v2-issues" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={palette.FIDESUI_WARNING} stopOpacity={0.6} /><stop offset="100%" stopColor={palette.FIDESUI_WARNING} stopOpacity={0.15} /></linearGradient>
          </defs>
          <CartesianGrid {...GRID} />
          <XAxis dataKey="month" axisLine={false} tickLine={false} tick={AXIS_TICK} />
          <YAxis domain={[0, 30]} axisLine={false} tickLine={false} tick={AXIS_TICK} />
          <Tooltip contentStyle={TT_STYLE} />
          <Area type="monotone" dataKey="healthy" name="Healthy" stroke={palette.FIDESUI_SUCCESS} strokeWidth={1.5} fill="url(#v2-healthy)" stackId="s" dot={false} />
          <Area type="monotone" dataKey="issues" name="Has Issues" stroke={palette.FIDESUI_WARNING} strokeWidth={1.5} fill="url(#v2-issues)" stackId="s" dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>

    <Divider className="!my-3" />

    {/* V3 */}
    <ChartLabel label="V3 — Issue Resolution (trending down)" />
    <Text type="secondary" className="!-mt-1 mb-1 text-[10px]">Story: we&apos;re resolving governance gaps. Which issue types are being fixed fastest?</Text>
    <Legend items={[
      { name: "No steward", color: palette.FIDESUI_TERRACOTTA },
      { name: "Unreviewed fields", color: palette.FIDESUI_SANDSTONE },
      { name: "No purposes", color: palette.FIDESUI_OLIVE },
      { name: "No integration", color: palette.FIDESUI_MINOS },
    ]} />
    <div className="h-[140px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={V3_DATA} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
          <defs>
            <linearGradient id="v3-a" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={palette.FIDESUI_TERRACOTTA} stopOpacity={0.6} /><stop offset="100%" stopColor={palette.FIDESUI_TERRACOTTA} stopOpacity={0.15} /></linearGradient>
            <linearGradient id="v3-b" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={palette.FIDESUI_SANDSTONE} stopOpacity={0.6} /><stop offset="100%" stopColor={palette.FIDESUI_SANDSTONE} stopOpacity={0.15} /></linearGradient>
            <linearGradient id="v3-c" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={palette.FIDESUI_OLIVE} stopOpacity={0.6} /><stop offset="100%" stopColor={palette.FIDESUI_OLIVE} stopOpacity={0.15} /></linearGradient>
            <linearGradient id="v3-d" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={palette.FIDESUI_MINOS} stopOpacity={0.6} /><stop offset="100%" stopColor={palette.FIDESUI_MINOS} stopOpacity={0.15} /></linearGradient>
          </defs>
          <CartesianGrid {...GRID} />
          <XAxis dataKey="month" axisLine={false} tickLine={false} tick={AXIS_TICK} />
          <YAxis domain={[0, 55]} axisLine={false} tickLine={false} tick={AXIS_TICK} />
          <Tooltip contentStyle={TT_STYLE} />
          <Area type="monotone" dataKey="noSteward" name="No steward" stroke={palette.FIDESUI_TERRACOTTA} strokeWidth={1} fill="url(#v3-a)" stackId="s" dot={false} />
          <Area type="monotone" dataKey="unreviewed" name="Unreviewed" stroke={palette.FIDESUI_SANDSTONE} strokeWidth={1} fill="url(#v3-b)" stackId="s" dot={false} />
          <Area type="monotone" dataKey="noPurpose" name="No purposes" stroke={palette.FIDESUI_OLIVE} strokeWidth={1} fill="url(#v3-c)" stackId="s" dot={false} />
          <Area type="monotone" dataKey="noIntegration" name="No integration" stroke={palette.FIDESUI_MINOS} strokeWidth={1} fill="url(#v3-d)" stackId="s" dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>

    <Divider className="!my-3" />

    {/* V4 */}
    <ChartLabel label="V4 — Dual: Score Line + Stacked Pillar Fill" />
    <Text type="secondary" className="!-mt-1 mb-1 text-[10px]">Bold line = overall score. Stacked fill = pillar composition. Best of both worlds.</Text>
    <Legend items={[...PILLARS, { name: "Overall", color: palette.FIDESUI_MINOS }]} />
    <div className="h-[140px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={V4_DATA} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
          <defs>
            {makeGrads("v4")}
            <linearGradient id="v4-overall" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={palette.FIDESUI_MINOS} stopOpacity={0} />
              <stop offset="100%" stopColor={palette.FIDESUI_MINOS} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid {...GRID} />
          <XAxis dataKey="month" axisLine={false} tickLine={false} tick={AXIS_TICK} />
          <YAxis domain={[0, 100]} axisLine={false} tickLine={false} tick={AXIS_TICK} />
          <Tooltip contentStyle={TT_STYLE} />
          {PILLARS.map((s) => <Area key={s.key} type="monotone" dataKey={s.key} name={s.name} stroke={s.color} strokeWidth={1} fill={`url(#v4-${s.key})`} stackId="s" dot={false} />)}
          <Area type="monotone" dataKey="overall" name="Overall" stroke={palette.FIDESUI_MINOS} strokeWidth={2.5} fill="url(#v4-overall)" dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  </Flex>
);

export default ChartVariants;
