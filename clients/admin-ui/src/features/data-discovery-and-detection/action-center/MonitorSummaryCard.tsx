import { Card, Flex, Progress, Tag, Typography } from "fidesui";
import { useMemo } from "react";

import { nFormatter, pluralize } from "~/features/common/utils";

import {
  FAKE_DATA_CATEGORIES,
  FAKE_DATA_USES,
  computePercent,
} from "./dashboardFakeData";
import { MonitorAggregatedResults } from "./types";
import { MONITOR_TYPES } from "./utils/getMonitorType";

const { Text } = Typography;

export type ColorScheme = "functional" | "brand";

export type CardLayout = "stat-grid" | "sparkline";

interface MonitorSummaryCardProps {
  type: MONITOR_TYPES;
  monitors: MonitorAggregatedResults[];
  colorScheme?: ColorScheme;
  layout?: CardLayout;
}

interface BreakdownItem {
  label: string;
  value: number;
}

interface TimeSeriesPoint {
  label: string;
  value: number;
}

const MONITOR_TYPE_CONFIG: Record<
  MONITOR_TYPES,
  {
    title: string;
    rateLabel: string;
    unit: [string, string];
    tagSection: { title: string; data: { label: string; value: number }[] };
    overall: {
      totalDiscovered: number;
      approved: number;
    };
    timeSeries: TimeSeriesPoint[];
    chartLabel: string;
    breakdownLabel: string;
    emptyDescription: string;
  }
> = {
  [MONITOR_TYPES.WEBSITE]: {
    title: "WEB MONITORS",
    rateLabel: "Resources approved",
    unit: ["resource", "resources"],
    tagSection: { title: "CATEGORIES OF CONSENT", data: FAKE_DATA_USES },
    overall: { totalDiscovered: 2_327, approved: 680 },
    chartLabel: "RESOURCES DETECTED",
    breakdownLabel: "CURRENT STATUS",
    emptyDescription:
      "Add a web monitor to start tracking cookies, tags, and other resources across your sites.",
    timeSeries: [
      { label: "Oct", value: 42 },
      { label: "Nov", value: 58 },
      { label: "Dec", value: 51 },
      { label: "Jan", value: 73 },
      { label: "Feb", value: 89 },
      { label: "Mar", value: 127 },
    ],
  },
  [MONITOR_TYPES.DATASTORE]: {
    title: "DATA STORES",
    rateLabel: "Resources approved",
    unit: ["resource", "resources"],
    tagSection: { title: "DATA CATEGORIES", data: FAKE_DATA_CATEGORIES },
    overall: { totalDiscovered: 52_853, approved: 34_000 },
    chartLabel: "RESOURCES DETECTED",
    breakdownLabel: "CURRENT STATUS",
    emptyDescription:
      "Connect a data store to begin discovering and classifying sensitive data fields.",
    timeSeries: [
      { label: "Oct", value: 1_820 },
      { label: "Nov", value: 2_140 },
      { label: "Dec", value: 2_580 },
      { label: "Jan", value: 3_010 },
      { label: "Feb", value: 3_490 },
      { label: "Mar", value: 3_853 },
    ],
  },
  [MONITOR_TYPES.INFRASTRUCTURE]: {
    title: "INFRASTRUCTURE",
    rateLabel: "Coverage",
    unit: ["system", "systems"],
    tagSection: { title: "DATA USES", data: FAKE_DATA_USES },
    overall: { totalDiscovered: 154, approved: 142 },
    chartLabel: "RESOURCES DETECTED",
    breakdownLabel: "CURRENT STATUS",
    emptyDescription:
      "Connect an identity provider to start monitoring systems and tracking coverage.",
    timeSeries: [
      { label: "Oct", value: 5 },
      { label: "Nov", value: 7 },
      { label: "Dec", value: 8 },
      { label: "Jan", value: 9 },
      { label: "Feb", value: 11 },
      { label: "Mar", value: 12 },
    ],
  },
};

// ── SVG Sparkline helpers ──

const buildSparklinePath = (
  points: number[],
  width: number,
  height: number,
  padding = 2,
): string => {
  if (points.length < 2) return "";
  const max = Math.max(...points);
  const min = Math.min(...points);
  const range = max - min || 1;
  const stepX = (width - padding * 2) / (points.length - 1);
  return points
    .map((v, i) => {
      const x = padding + i * stepX;
      const y = padding + (1 - (v - min) / range) * (height - padding * 2);
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
};

const buildAreaPath = (
  points: number[],
  width: number,
  height: number,
  padding = 2,
): string => {
  const linePath = buildSparklinePath(points, width, height, padding);
  if (!linePath) return "";
  const lastX =
    padding + (points.length - 1) * ((width - padding * 2) / (points.length - 1));
  return `${linePath} L${lastX.toFixed(1)},${(height - padding).toFixed(1)} L${padding},${(height - padding).toFixed(1)} Z`;
};

const getBreakdownItems = (
  type: MONITOR_TYPES,
  monitors: MonitorAggregatedResults[],
): BreakdownItem[] => {
  if (type === MONITOR_TYPES.DATASTORE) {
    let unlabeled = 0;
    let classifying = 0;
    let classified = 0;
    let reviewed = 0;
    for (const m of monitors) {
      const u = m.updates as {
        unlabeled?: number;
        in_review?: number;
        classifying?: number;
        reviewed?: number;
        removals?: number;
      };
      unlabeled += u.unlabeled ?? 0;
      classifying += u.classifying ?? 0;
      classified += u.in_review ?? 0;
      reviewed += u.reviewed ?? 0;
    }
    return [
      { label: "unlabeled", value: unlabeled },
      { label: "classifying", value: classifying },
      { label: "classified", value: classified },
      { label: "reviewed", value: reviewed },
    ].filter((s) => s.value > 0);
  }

  if (type === MONITOR_TYPES.WEBSITE) {
    let cookies = 0;
    let tags = 0;
    let pixels = 0;
    let iframes = 0;
    let requests = 0;
    for (const m of monitors) {
      const u = m.updates as {
        cookie?: number;
        browser_request?: number;
        image?: number;
        iframe?: number;
        javascript_tag?: number;
      };
      cookies += u.cookie ?? 0;
      tags += u.javascript_tag ?? 0;
      pixels += u.image ?? 0;
      iframes += u.iframe ?? 0;
      requests += u.browser_request ?? 0;
    }
    return [
      { label: "cookies", value: cookies },
      { label: "tags", value: tags },
      { label: "pixels", value: pixels },
      { label: "iframes", value: iframes },
      { label: "requests", value: requests },
    ].filter((s) => s.value > 0);
  }

  // Infrastructure: known vs unknown systems
  let infraTotal = 0;
  for (const m of monitors) {
    infraTotal += m.total_updates ?? 0;
  }
  const known = Math.round(infraTotal * 0.9);
  const unknown = infraTotal - known;
  return [
    { label: "known", value: known },
    { label: "unknown", value: unknown },
  ].filter((s) => s.value > 0);
};

const getCompletionRate = (
  overall: { totalDiscovered: number; approved: number },
): { approved: number; total: number; percent: number } => {
  const { totalDiscovered: total, approved } = overall;
  const percent = total > 0 ? Math.round((approved / total) * 100) : 0;
  return { approved, total, percent };
};

const getStrokeColor = (percent: number): string => {
  if (percent >= 75) return "#5a9a68";
  if (percent >= 40) return "#e59d47";
  return "#d9534f";
};

// Carbon "wikis" icon (32×32) — globe
const WIKIS_ICON = (
  <path d="M16,2A14,14,0,1,0,30,16,14,14,0,0,0,16,2ZM28,15H22A24.26,24.26,0,0,0,19.21,4.45,12,12,0,0,1,28,15ZM16,28a5,5,0,0,1-.67,0A21.85,21.85,0,0,1,12,17H20a21.85,21.85,0,0,1-3.3,11A5,5,0,0,1,16,28ZM12,15a21.85,21.85,0,0,1,3.3-11,6,6,0,0,1,1.34,0A21.85,21.85,0,0,1,20,15Zm.76-10.55A24.26,24.26,0,0,0,10,15h-6A12,12,0,0,1,12.79,4.45ZM4.05,17h6a24.26,24.26,0,0,0,2.75,10.55A12,12,0,0,1,4.05,17ZM19.21,27.55A24.26,24.26,0,0,0,22,17h6A12,12,0,0,1,19.21,27.55Z" />
);

// Carbon "data--base" icon (32×32) — server rack
const DATABASE_ICON = (
  <>
    <path d="M24,3H8A2,2,0,0,0,6,5V27a2,2,0,0,0,2,2H24a2,2,0,0,0,2-2V5A2,2,0,0,0,24,3Zm0,2v6H8V5ZM8,19V13H24v6Zm0,8V21H24v6Z" />
    <circle cx="11" cy="8" r="1" />
    <circle cx="11" cy="16" r="1" />
    <circle cx="11" cy="24" r="1" />
  </>
);

// Carbon "transform--instructions" icon (32×32) — gear with arc
const TRANSFORM_INSTRUCTIONS_ICON = (
  <>
    <path d="M23,17v-2h-2.1c-0.1-0.6-0.4-1.2-0.7-1.8l1.5-1.5l-1.4-1.4l-1.5,1.5c-0.5-0.3-1.1-0.6-1.8-0.7V9h-2v2.1c-0.6,0.1-1.2,0.4-1.8,0.7l-1.5-1.5l-1.4,1.4l1.5,1.5c-0.3,0.5-0.6,1.1-0.7,1.8H9v2h2.1c0.1,0.6,0.4,1.2,0.7,1.8l-1.5,1.5l1.4,1.4l1.5-1.5c0.5,0.3,1.1,0.6,1.8,0.7V23h2v-2.1c0.6-0.1,1.2-0.4,1.8-0.7l1.5,1.5l1.4-1.4l-1.5-1.5c0.3-0.5,0.6-1.1,0.7-1.8H23z M16,19c-1.7,0-3-1.3-3-3s1.3-3,3-3s3,1.3,3,3S17.7,19,16,19z" />
    <path d="M16,2v2c6.6,0,12,5.4,12,12s-5.4,12-12,12v2c7.7,0,14-6.3,14-14S23.7,2,16,2z" />
    <path d="M8.2,25.1L7,26.7c1.2,1,2.6,1.9,4.2,2.4l0.7-1.9C10.5,26.7,9.3,26,8.2,25.1z" />
    <path d="M4.2,18l-2,0.4C2.5,20,3.1,21.6,3.9,23l1.7-1C4.9,20.8,4.4,19.4,4.2,18z" />
    <path d="M5.6,10L3.9,9c-0.8,1.4-1.4,3-1.6,4.6l2,0.3C4.4,12.5,4.9,11.2,5.6,10z" />
    <path d="M11.8,4.8l-0.7-1.9C9.6,3.5,8.2,4.3,7,5.3l1.3,1.5C9.3,6,10.5,5.3,11.8,4.8z" />
  </>
);

const MonitorSummaryCard = ({
  type,
  monitors,
  layout = "sparkline",
}: MonitorSummaryCardProps) => {
  const config = MONITOR_TYPE_CONFIG[type];
  if (!config) {
    return null;
  }

  const hasData = monitors.length > 0;
  const monitorUpdatesTotal = monitors.reduce(
    (sum, m) => sum + (m.total_updates ?? 0),
    0,
  );
  const isLowData = hasData && monitorUpdatesTotal < 50;

  const { approved, total, percent } = useMemo(() => {
    if (!hasData) return { approved: 0, total: 0, percent: 0 };
    if (isLowData) {
      return {
        approved: monitorUpdatesTotal,
        total: monitorUpdatesTotal,
        percent: 100,
      };
    }
    return getCompletionRate(config.overall);
  }, [config.overall, hasData, isLowData, monitorUpdatesTotal]);
  const items = useMemo(
    () => (hasData ? getBreakdownItems(type, monitors) : []),
    [type, monitors, hasData],
  );

  const monitorCount = monitors.length;
  const { tagSection, overall } = config;
  const tagTotal = tagSection.data.reduce((s, d) => s + d.value, 0);
  const attentionCount =
    hasData && !isLowData ? overall.totalDiscovered - overall.approved : 0;

  const EMPTY_ICONS: Record<MONITOR_TYPES, React.ReactNode> = {
    [MONITOR_TYPES.WEBSITE]: WIKIS_ICON,
    [MONITOR_TYPES.DATASTORE]: DATABASE_ICON,
    [MONITOR_TYPES.INFRASTRUCTURE]: TRANSFORM_INSTRUCTIONS_ICON,
  };

  // ── Empty state ──
  const emptyState = (
    <Flex
      vertical
      align="center"
      justify="center"
      gap={12}
      className="py-6 px-4"
    >
      <svg
        width="40"
        height="40"
        viewBox="0 0 32 32"
        fill="#d1d2d4"
      >
        {EMPTY_ICONS[type]}
      </svg>
      <Text type="secondary" className="text-xs text-center leading-relaxed">
        {config.emptyDescription}
      </Text>
    </Flex>
  );

  // ── Tags section (only shown when there's enough data) ──
  const tagsSection =
    hasData && !isLowData ? (
      <div className="mt-3 pt-3 border-t border-neutral-100">
        <Text
          className="text-[10px] tracking-[0.1em] mb-2 block"
          type="secondary"
          strong
        >
          {tagSection.title}
        </Text>
        <Flex gap={4} wrap="wrap">
          {tagSection.data.map((item) => (
            <Tag key={item.label} className="text-[11px]">
              {item.label} {computePercent(item.value, tagTotal)}%
            </Tag>
          ))}
        </Flex>
      </div>
    ) : null;

  // ── Breakdown section (only shown when there's data) ──
  const breakdownSection =
    hasData && items.length > 0 && !isLowData ? (
      <div className="mt-4 pt-3 border-t border-neutral-100">
        <Text
          className="text-[10px] tracking-[0.1em] mb-1.5 block"
          type="secondary"
          strong
        >
          {config.breakdownLabel}
        </Text>
        <Text className="text-[11px]" type="secondary">
          {items
            .map((item) => `${nFormatter(item.value)} ${item.label}`)
            .join(" · ")}
        </Text>
      </div>
    ) : null;

  // ── "No action required" for low data state ──
  const noActionRequired = isLowData ? (
    <div className="mt-4 pt-3 border-t border-neutral-100">
      <Flex align="center" justify="center" gap={6} className="py-2">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="7" stroke="#5a9a68" strokeWidth="1.5" />
          <path d="M5 8l2 2 4-4" stroke="#5a9a68" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <Text className="text-[12px] font-medium" style={{ color: "#5a9a68" }}>
          No action required
        </Text>
      </Flex>
    </div>
  ) : null;

  // ── Stat Grid layout (infrastructure) ──
  if (layout === "stat-grid") {
    if (!hasData) {
      return (
        <Card
          className="rounded-lg"
          styles={{ body: { padding: "14px 20px" } }}
        >
          <Text
            className="text-[10px] tracking-[0.1em] mb-1 block"
            type="secondary"
            strong
          >
            {config.title}
          </Text>
          {emptyState}
        </Card>
      );
    }

    return (
      <Card className="rounded-lg" styles={{ body: { padding: "14px 20px" } }}>
        <Flex align="center" justify="space-between" className="mb-4">
          <Text
            className="text-[10px] tracking-[0.1em]"
            type="secondary"
            strong
          >
            {config.title}
          </Text>
          <Text type="secondary" className="text-[10px]">
            {monitorCount} {pluralize(monitorCount, "monitor", "monitors")}
          </Text>
        </Flex>

        <div className="grid grid-cols-2 gap-1.5">
          <div className="rounded-md bg-neutral-50 px-2.5 py-2">
            <Text className="text-sm font-bold block leading-tight">
              {nFormatter(total)}
            </Text>
            <Text type="secondary" className="text-[10px]">
              Total systems
            </Text>
          </div>
          <div className="rounded-md bg-neutral-50 px-2.5 py-2">
            <Text
              className="text-sm font-bold block leading-tight"
              style={{ color: attentionCount > 0 ? "#e59d47" : undefined }}
            >
              {nFormatter(attentionCount)}
            </Text>
            <Text type="secondary" className="text-[10px]">
              Need attention
            </Text>
          </div>
          <div className="rounded-md bg-neutral-50 px-2.5 py-2">
            <Text
              className="text-sm font-bold block leading-tight"
              style={{ color: "#5a9a68" }}
            >
              {nFormatter(approved)}
            </Text>
            <Text type="secondary" className="text-[10px]">
              Approved
            </Text>
          </div>
          <div className="rounded-md bg-neutral-50 px-2.5 py-2">
            <Text className="text-sm font-bold block leading-tight">
              {percent}%
            </Text>
            <Text type="secondary" className="text-[10px]">
              {config.rateLabel}
            </Text>
          </div>
        </div>

        {breakdownSection}
        {noActionRequired}
        {tagsSection}
      </Card>
    );
  }

  // ── Sparkline layout (datastores, web monitors) ──
  if (!hasData) {
    return (
      <Card className="rounded-lg" styles={{ body: { padding: "14px 20px" } }}>
        <Text
          className="text-[10px] tracking-[0.1em] mb-1 block"
          type="secondary"
          strong
        >
          {config.title}
        </Text>
        {emptyState}
      </Card>
    );
  }

  const tsValues = config.timeSeries.map((p) => p.value);
  const tsLabels = config.timeSeries.map((p) => p.label);
  const tsLatest = tsValues[tsValues.length - 1] ?? 0;
  const tsPrev = tsValues[tsValues.length - 2] ?? tsLatest;
  const tsDelta =
    tsPrev > 0 ? Math.round(((tsLatest - tsPrev) / tsPrev) * 100) : 0;
  const tsDeltaColor = tsDelta >= 0 ? "#5a9a68" : "#d9534f";
  const tsDeltaSign = tsDelta >= 0 ? "+" : "";
  const sparkW = 260;
  const sparkH = 80;

  return (
    <Card className="rounded-lg" styles={{ body: { padding: "14px 20px" } }}>
      <Flex align="center" justify="space-between" className="mb-3">
        <Text
          className="text-[10px] tracking-[0.1em]"
          type="secondary"
          strong
        >
          {config.title}
        </Text>
        <Text type="secondary" className="text-[10px]">
          {monitorCount} {pluralize(monitorCount, "monitor", "monitors")}
        </Text>
      </Flex>

      <Flex align="start" gap={20}>
        {/* Circle progress + rate info */}
        <Flex vertical align="center" gap={4} className="shrink-0">
          <Progress
            type="circle"
            percent={percent}
            size={80}
            strokeWidth={8}
            strokeColor={getStrokeColor(percent)}
            format={(pct) => (
              <span className="text-lg font-bold">{pct}%</span>
            )}
          />
          <Text type="secondary" className="text-[10px] text-center">
            {config.rateLabel}
          </Text>
          <Text strong className="text-[11px] text-center">
            {nFormatter(approved, 1)} of {nFormatter(total, 1)}
          </Text>
        </Flex>

        {/* Sparkline area chart */}
        <Flex vertical gap={2} className="flex-1 min-w-0">
          <Flex align="center" justify="space-between">
            <Text
              className="text-[10px] tracking-[0.1em]"
              type="secondary"
              strong
            >
              {config.chartLabel}
            </Text>
            <Text
              className="text-[11px] font-semibold"
              style={{ color: tsDeltaColor }}
            >
              {tsDeltaSign}{tsDelta}% vs last mo
            </Text>
          </Flex>
          <svg
            viewBox={`0 0 ${sparkW} ${sparkH}`}
            className="w-full"
            style={{ height: sparkH }}
          >
            <defs>
              <linearGradient id={`areaGrad-${type}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#cecac2" stopOpacity={0.5} />
                <stop offset="100%" stopColor="#cecac2" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <path
              d={buildAreaPath(tsValues, sparkW, sparkH)}
              fill={`url(#areaGrad-${type})`}
            />
            <path
              d={buildSparklinePath(tsValues, sparkW, sparkH)}
              fill="none"
              stroke="#cecac2"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            {tsValues.map((v, i) => {
              const pad = 2;
              const stepX = (sparkW - pad * 2) / (tsValues.length - 1);
              const min = Math.min(...tsValues);
              const range = Math.max(...tsValues) - min || 1;
              const cx = pad + i * stepX;
              const cy = pad + (1 - (v - min) / range) * (sparkH - pad * 2);
              return (
                <circle
                  key={tsLabels[i]}
                  cx={cx}
                  cy={cy}
                  r={3}
                  fill="#cecac2"
                />
              );
            })}
          </svg>
          <Flex justify="space-between">
            {tsLabels.map((l) => (
              <Text key={l} className="text-[9px]" type="secondary">
                {l}
              </Text>
            ))}
          </Flex>
        </Flex>
      </Flex>

      {breakdownSection}
      {noActionRequired}
      {tagsSection}
    </Card>
  );
};

export default MonitorSummaryCard;
