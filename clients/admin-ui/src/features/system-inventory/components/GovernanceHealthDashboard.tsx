import { Avatar, Divider, Flex, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useMemo } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getBrandIconUrl } from "~/features/common/utils";

import { PILLAR_CONFIG } from "../constants";
import { type GovernanceHealthData, type MockSystem, PillarKey } from "../types";
import GovernanceScoreCard from "./GovernanceScoreCard";

interface GovernanceHealthDashboardProps {
  data: GovernanceHealthData;
  systems: MockSystem[];
}

// Each pillar contributes score/3 so they stack to the overall score.
// Historical months are hardcoded; the final month is derived from live data.
type TrendPoint = {
  month: string;
  [PillarKey.COVERAGE]: number;
  [PillarKey.CLASSIFICATION]: number;
  [PillarKey.RISK]: number;
};

const TREND_HISTORY: TrendPoint[] = [
  { month: "Oct", coverage: 12, classification: 10, risk: 12 },
  { month: "Nov", coverage: 14, classification: 12, risk: 15 },
  { month: "Dec", coverage: 17, classification: 15, risk: 18 },
  { month: "Jan", coverage: 20, classification: 18, risk: 20 },
  { month: "Feb", coverage: 23, classification: 21, risk: 23 },
];

function buildTrendData(data: GovernanceHealthData): TrendPoint[] {
  const dimScore = (key: PillarKey) =>
    Math.round((data.dimensions.find((d) => d.key === key)?.score ?? 0) / 3);
  return [
    ...TREND_HISTORY,
    {
      month: "Mar",
      [PillarKey.COVERAGE]: dimScore(PillarKey.COVERAGE),
      [PillarKey.CLASSIFICATION]: dimScore(PillarKey.CLASSIFICATION),
      [PillarKey.RISK]: dimScore(PillarKey.RISK),
    },
  ];
}

const PILLAR_SERIES: { key: PillarKey; name: string; color: string }[] = [
  {
    key: PillarKey.COVERAGE,
    name: PILLAR_CONFIG[PillarKey.COVERAGE].label,
    color: PILLAR_CONFIG[PillarKey.COVERAGE].color,
  },
  {
    key: PillarKey.CLASSIFICATION,
    name: PILLAR_CONFIG[PillarKey.CLASSIFICATION].label,
    color: PILLAR_CONFIG[PillarKey.CLASSIFICATION].color,
  },
  {
    key: PillarKey.RISK,
    name: PILLAR_CONFIG[PillarKey.RISK].label,
    color: PILLAR_CONFIG[PillarKey.RISK].color,
  },
];

interface ActivityItem {
  message: string;
  time: string;
  color: string;
  steward: { initials: string };
  system: {
    name: string;
    logoDomain: string | null;
    logoUrl?: string;
  };
}

const CATEGORY_COLORS: Record<string, string> = {
  classification: palette.FIDESUI_SUCCESS,
  integration: palette.FIDESUI_INFO,
  system: palette.FIDESUI_INFO,
  steward: palette.FIDESUI_INFO,
  purpose: palette.FIDESUI_SUCCESS,
};

function formatRelativeTime(timestamp: string): string {
  const diff = Date.now() - new Date(timestamp).getTime();
  const hours = Math.floor(diff / (1000 * 60 * 60));
  if (hours < 1) return "just now";
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  const weeks = Math.floor(days / 7);
  return `${weeks}w ago`;
}

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

function buildActivity(systems: MockSystem[]): ActivityItem[] {
  const entries = systems.flatMap((sys) =>
    sys.history.map((h) => ({
      ...h,
      systemName: sys.name,
      logoDomain: sys.logoDomain,
      logoUrl: sys.logoUrl,
    })),
  );
  entries.sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
  );
  return entries.slice(0, 5).map((entry) => ({
    message: `${entry.action}: ${entry.detail}`,
    time: formatRelativeTime(entry.timestamp),
    color: CATEGORY_COLORS[entry.category] ?? palette.FIDESUI_NEUTRAL_500,
    steward: { initials: entry.user === "System" ? "SY" : getInitials(entry.user) },
    system: {
      name: entry.systemName,
      logoDomain: entry.logoDomain,
      logoUrl: entry.logoUrl,
    },
  }));
}

const GovernanceHealthDashboard = ({
  data,
  systems,
}: GovernanceHealthDashboardProps) => {
  const trendData = buildTrendData(data);
  const activity = useMemo(() => buildActivity(systems), [systems]);

  return (
    <div className="mb-2">
      <Flex gap={32}>
        {/* Panel 1: Donut + legend */}
        <div className="shrink-0">
          <GovernanceScoreCard data={data} />
        </div>

        {/* Panel 2: Health Over Time (stacked pillar contributions) */}
        <div
          className="min-w-0 flex-1 border-l border-solid pl-8"
          style={{ borderColor: palette.FIDESUI_NEUTRAL_100 }}
        >
          <Flex justify="space-between" align="center" className="mb-6">
            <Text strong className="text-[10px] uppercase tracking-wider">
              Health over time
            </Text>
            <Flex gap={12}>
              {PILLAR_SERIES.map((series) => (
                <Flex key={series.key} align="center" gap={4}>
                  <div
                    className="size-[5px] shrink-0 rounded-full"
                    style={{ backgroundColor: series.color }}
                  />
                  <Text
                    className="text-[10px]"
                    style={{ color: palette.FIDESUI_MINOS }}
                  >
                    {series.name}
                  </Text>
                </Flex>
              ))}
            </Flex>
          </Flex>
          <div className="h-[170px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={trendData}
                margin={{ top: 4, right: 4, bottom: 0, left: -20 }}
              >
                <defs>
                  {PILLAR_SERIES.map((series) => (
                    <linearGradient
                      key={series.key}
                      id={`dash-grad-${series.key}`}
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="0%"
                        stopColor={series.color}
                        stopOpacity={0.7}
                      />
                      <stop
                        offset="100%"
                        stopColor={series.color}
                        stopOpacity={0.2}
                      />
                    </linearGradient>
                  ))}
                </defs>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke={palette.FIDESUI_NEUTRAL_100}
                  vertical={false}
                />
                <XAxis
                  dataKey="month"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 10, fill: palette.FIDESUI_NEUTRAL_500 }}
                />
                <YAxis
                  domain={[0, 100]}
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 10, fill: palette.FIDESUI_NEUTRAL_500 }}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: 6,
                    border: `1px solid ${palette.FIDESUI_NEUTRAL_100}`,
                    fontSize: 11,
                  }}
                />
                {PILLAR_SERIES.map((series) => (
                  <Area
                    key={series.key}
                    type="monotone"
                    dataKey={series.key}
                    name={series.name}
                    stroke={series.color}
                    strokeWidth={1}
                    fill={`url(#dash-grad-${series.key})`}
                    stackId="health"
                    dot={false}
                  />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Panel 3: Recent activity */}
        <div
          className="min-w-0 flex-1 border-l border-solid pl-8"
          style={{ borderColor: palette.FIDESUI_NEUTRAL_100 }}
        >
          <Text
            strong
            className="mb-3 block text-[10px] uppercase tracking-wider"
          >
            Recent activity
          </Text>
          <Flex vertical gap={0}>
            {activity.map((item, idx) => (
              <Flex
                key={`${item.time}-${idx}`}
                justify="space-between"
                align="center"
                className="border-b border-solid py-1.5 last:border-b-0"
                style={{ borderColor: palette.FIDESUI_NEUTRAL_75 }}
              >
                <Flex align="center" gap={8} className="min-w-0 flex-1">
                  <Avatar
                    size={20}
                    shape="square"
                    src={
                      item.system.logoUrl ??
                      (item.system.logoDomain
                        ? getBrandIconUrl(item.system.logoDomain, 40)
                        : undefined)
                    }
                    style={
                      !item.system.logoDomain && !item.system.logoUrl
                        ? {
                            backgroundColor: palette.FIDESUI_NEUTRAL_100,
                            color: palette.FIDESUI_NEUTRAL_800,
                            fontSize: 9,
                          }
                        : undefined
                    }
                    className="shrink-0"
                  >
                    {!item.system.logoDomain && !item.system.logoUrl
                      ? item.system.name.slice(0, 2).toUpperCase()
                      : null}
                  </Avatar>
                  <Text className="min-w-0 flex-1 truncate text-[11px]">
                    {item.message}
                  </Text>
                </Flex>
                <Flex align="center" className="shrink-0 pl-4">
                  <Text
                    type="secondary"
                    className="w-[48px] text-right text-xs"
                  >
                    {item.time}
                  </Text>
                  <Text
                    className="w-[52px] cursor-pointer text-right text-xs"
                    style={{ color: palette.FIDESUI_MINOS }}
                  >
                    View &rarr;
                  </Text>
                </Flex>
              </Flex>
            ))}
          </Flex>
        </div>
      </Flex>

      <Divider className="!mb-0 !mt-4" />
    </div>
  );
};

export default GovernanceHealthDashboard;
