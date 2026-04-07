import { Avatar, Divider, Flex, Progress, Statistic, Tag, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
} from "recharts";

import { useCountUp } from "~/home/useCountUp";

import type { GovernanceHealthData } from "../types";

// --- Shared constants ---

const COLORS = [
  palette.FIDESUI_TERRACOTTA,
  palette.FIDESUI_OLIVE,
  palette.FIDESUI_SANDSTONE,
  palette.FIDESUI_MINOS,
];
const DELTAS = ["+5", "+3", "+1", "-2"];

const TREND = [
  { m: "Oct", v: 48 }, { m: "Nov", v: 53 }, { m: "Dec", v: 58 },
  { m: "Jan", v: 64 }, { m: "Feb", v: 69 }, { m: "Mar", v: 75 },
];

interface Act { msg: string; t: string; c: string; s: string }
const ACTS: Act[] = [
  { msg: "Stripe annotations completed", t: "2h", c: palette.FIDESUI_SUCCESS, s: "MB" },
  { msg: "3 issues flagged in Salesforce", t: "5h", c: palette.FIDESUI_WARNING, s: "LT" },
  { msg: "Purposes updated for marketing", t: "1d", c: palette.FIDESUI_SUCCESS, s: "RS" },
  { msg: "Steward assigned to Segment", t: "1d", c: palette.FIDESUI_INFO, s: "RS" },
  { msg: "Governance review completed", t: "3d", c: palette.FIDESUI_INFO, s: "AK" },
];

const Dot = ({ color }: { color: string }) => (
  <div className="size-[5px] shrink-0 rounded-full" style={{ backgroundColor: color }} />
);

const Av = ({ s }: { s: string }) => (
  <Avatar size={18} style={{ backgroundColor: "#e6e6e8", color: "#53575c", fontSize: 8 }}>{s}</Avatar>
);

const Delta = ({ d }: { d: string }) => (
  <Text className="text-[10px]" style={{ color: d.startsWith("-") ? palette.FIDESUI_ERROR : palette.FIDESUI_SUCCESS }}>
    {d}
  </Text>
);

// ===================================================================
// VARIANT A — "Executive Strip"
// Single dense row: Score | Sparkline | 4 Pillar mini-stats | Activity ticker
// No wasted space — every pixel earns its keep
// ===================================================================

const VariantA = ({ data }: { data: GovernanceHealthData }) => {
  const score = useCountUp(data.score);
  const total = data.healthBreakdown.healthy + data.healthBreakdown.issues;

  return (
    <Flex align="center" gap={0} className="h-[120px]">
      {/* Score block */}
      <Flex vertical justify="center" className="shrink-0 pr-6">
        <Flex align="baseline" gap={2}>
          <Statistic value={score} className="[&_.ant-statistic-content-value]:!text-[42px] [&_.ant-statistic-content-value]:!font-bold [&_.ant-statistic-content-value]:!leading-none" />
          <Text type="secondary" className="text-[11px]">/100</Text>
        </Flex>
        <Flex align="center" gap={6} className="mt-1">
          <Tag bordered={false} style={{ backgroundColor: "rgba(90,154,104,0.12)", color: "#5a9a68" }} className="!px-1.5 !py-0 !text-[10px]">▲5%</Tag>
          <Text type="secondary" className="text-[10px]">{total} sys · {data.totalIssues} issues</Text>
        </Flex>
      </Flex>

      {/* Inline sparkline */}
      <div className="h-[50px] w-[120px] shrink-0 border-l border-solid border-[#f0f0f0] pl-4">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={TREND} margin={{ top: 2, right: 0, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id="a-g" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#2b2e35" stopOpacity={0.2} />
                <stop offset="100%" stopColor="#2b2e35" stopOpacity={0} />
              </linearGradient>
            </defs>
            <Area type="monotone" dataKey="v" stroke="#2b2e35" strokeWidth={1.5} fill="url(#a-g)" dot={false} />
          </AreaChart>
        </ResponsiveContainer>
        <Text type="secondary" className="-mt-0.5 block text-center text-[9px]">6mo trend</Text>
      </div>

      {/* 4 pillar stats — tight grid */}
      <Flex className="shrink-0 border-l border-solid border-[#f0f0f0] pl-6" gap={16}>
        {data.dimensions.map((dim, i) => (
          <Flex key={dim.label} vertical align="center" gap={2} className="w-[60px]">
            <Progress
              type="circle"
              percent={dim.score}
              size={36}
              strokeColor={COLORS[i]}
              strokeWidth={10}
              format={(p) => <Text className="!text-[9px] !font-semibold">{p}</Text>}
            />
            <Text className="text-[9px] leading-none" style={{ color: palette.FIDESUI_MINOS }}>{dim.label}</Text>
            <Delta d={DELTAS[i]} />
          </Flex>
        ))}
      </Flex>

      {/* Activity — compact, scrollable feel */}
      <div className="ml-6 min-w-0 flex-1 border-l border-solid border-[#f0f0f0] pl-6">
        <Flex vertical gap={0}>
          {ACTS.map((a, i) => (
            <Flex key={i} align="center" gap={6} className="border-b border-solid border-[#f8f8f8] py-[5px] last:border-b-0">
              <Dot color={a.c} />
              <Text className="min-w-0 flex-1 truncate text-[11px]">{a.msg}</Text>
              <Av s={a.s} />
              <Text type="secondary" className="w-[20px] text-right text-[10px]">{a.t}</Text>
            </Flex>
          ))}
        </Flex>
      </div>
    </Flex>
  );
};

// ===================================================================
// VARIANT B — "Data Wall"
// Score with stacked bar behind it | Horizontal pillar bars fill center | Activity condensed right
// Everything edge-to-edge, no labels that don't earn space
// ===================================================================

const VariantB = ({ data }: { data: GovernanceHealthData }) => {
  const score = useCountUp(data.score);
  const total = data.healthBreakdown.healthy + data.healthBreakdown.issues;

  const barData = data.dimensions.map((dim) => ({
    name: dim.label,
    value: dim.score,
  }));

  return (
    <Flex align="stretch" gap={0} className="h-[120px]">
      {/* Score + stacked composition bar */}
      <Flex vertical justify="center" className="w-[200px] shrink-0 pr-6">
        <Flex align="baseline" gap={2}>
          <Statistic value={score} className="[&_.ant-statistic-content-value]:!text-[42px] [&_.ant-statistic-content-value]:!font-bold [&_.ant-statistic-content-value]:!leading-none" />
          <Text type="secondary" className="text-[11px]">/100</Text>
        </Flex>
        <Text type="secondary" className="text-[11px]">Inventory health</Text>
        {/* Composition bar — shows pillar proportions at a glance */}
        <Flex className="mt-2 h-[6px] w-full overflow-hidden rounded-full">
          {data.dimensions.map((dim, i) => (
            <div
              key={dim.label}
              style={{
                width: `${dim.score / data.dimensions.reduce((s, d) => s + d.score, 0) * 100}%`,
                backgroundColor: COLORS[i],
              }}
            />
          ))}
        </Flex>
        <Flex align="center" gap={6} className="mt-1.5">
          <Tag bordered={false} style={{ backgroundColor: "rgba(90,154,104,0.12)", color: "#5a9a68" }} className="!px-1.5 !py-0 !text-[10px]">▲5%</Tag>
          <Text type="secondary" className="text-[10px]">{total} sys · {data.totalIssues} issues</Text>
        </Flex>
      </Flex>

      {/* Horizontal bar chart — fills center */}
      <div className="flex min-w-0 flex-1 items-center border-l border-solid border-[#f0f0f0] px-6">
        <div className="h-[100px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={barData} layout="vertical" margin={{ top: 0, right: 30, bottom: 0, left: 0 }} barCategoryGap="25%">
              <XAxis type="number" domain={[0, 100]} hide />
              <Tooltip
                contentStyle={{ borderRadius: 6, border: "1px solid #f0f0f0", fontSize: 11 }}
                formatter={(value) => [`${value}%`]}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={14} background={{ fill: "#f5f5f5", radius: 4 }} label={{ position: "right", fontSize: 10, fill: "#53575c", formatter: (v) => `${v}%` }}>
                {barData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Activity — tight right column */}
      <div className="w-[320px] shrink-0 border-l border-solid border-[#f0f0f0] pl-6">
        <Flex vertical gap={0} className="h-full justify-center">
          {ACTS.map((a, i) => (
            <Flex key={i} align="center" gap={6} className="border-b border-solid border-[#f8f8f8] py-[5px] last:border-b-0">
              <Dot color={a.c} />
              <Text className="min-w-0 flex-1 truncate text-[11px]">{a.msg}</Text>
              <Av s={a.s} />
              <Text type="secondary" className="text-[10px]">{a.t}</Text>
            </Flex>
          ))}
        </Flex>
      </div>
    </Flex>
  );
};

// ===================================================================
// VARIANT C — "Donut Command Center"
// Padded donut left with score inside | Pillar legend inline | Trend sparkline | Activity
// Everything in one tight 100px-tall band
// ===================================================================

const VariantC = ({ data }: { data: GovernanceHealthData }) => {
  const score = useCountUp(data.score);
  const total = data.healthBreakdown.healthy + data.healthBreakdown.issues;

  const pieData = data.dimensions.map((dim, i) => ({
    name: dim.label,
    value: dim.score,
    color: COLORS[i],
  }));

  return (
    <Flex align="center" gap={0} className="h-[120px]">
      {/* Donut with score */}
      <div className="relative size-[100px] shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              innerRadius={30}
              outerRadius={46}
              paddingAngle={3}
              dataKey="value"
              startAngle={90}
              endAngle={-270}
              stroke="none"
              cornerRadius={4}
            >
              {pieData.map((e) => <Cell key={e.name} fill={e.color} />)}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex items-center justify-center">
          <Statistic value={score} className="[&_.ant-statistic-content-value]:!text-lg [&_.ant-statistic-content-value]:!font-bold" />
        </div>
      </div>

      {/* Score meta + pillar legend */}
      <Flex vertical justify="center" gap={4} className="shrink-0 pl-4 pr-6">
        <Text strong className="text-[11px]">Inventory health</Text>
        <Flex align="center" gap={4}>
          <Tag bordered={false} style={{ backgroundColor: "rgba(90,154,104,0.12)", color: "#5a9a68" }} className="!px-1.5 !py-0 !text-[9px]">▲5%</Tag>
          <Text type="secondary" className="text-[9px]">{total} sys · {data.totalIssues} issues</Text>
        </Flex>
        {data.dimensions.map((dim, i) => (
          <Flex key={dim.label} align="center" gap={4}>
            <div className="size-[5px] shrink-0 rounded-full" style={{ backgroundColor: COLORS[i] }} />
            <Text className="text-[9px]" style={{ color: palette.FIDESUI_MINOS }}>
              {dim.label} <Text strong className="text-[9px]">{dim.score}%</Text>
            </Text>
            <Delta d={DELTAS[i]} />
          </Flex>
        ))}
      </Flex>

      {/* Trend area — fills middle */}
      <div className="h-[80px] min-w-0 flex-1 border-l border-solid border-[#f0f0f0] px-4">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={TREND} margin={{ top: 4, right: 0, bottom: 14, left: 0 }}>
            <defs>
              <linearGradient id="c-g" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#2b2e35" stopOpacity={0.18} />
                <stop offset="100%" stopColor="#2b2e35" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="m" axisLine={false} tickLine={false} tick={{ fontSize: 9, fill: "#93969a" }} />
            <Area type="monotone" dataKey="v" stroke="#2b2e35" strokeWidth={1.5} fill="url(#c-g)" dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Activity */}
      <div className="w-[320px] shrink-0 border-l border-solid border-[#f0f0f0] pl-6">
        <Flex vertical gap={0}>
          {ACTS.map((a, i) => (
            <Flex key={i} align="center" gap={6} className="border-b border-solid border-[#f8f8f8] py-[5px] last:border-b-0">
              <Dot color={a.c} />
              <Text className="min-w-0 flex-1 truncate text-[11px]">{a.msg}</Text>
              <Av s={a.s} />
              <Text type="secondary" className="w-[20px] text-right text-[10px]">{a.t}</Text>
            </Flex>
          ))}
        </Flex>
      </div>
    </Flex>
  );
};

// ===================================================================
// Container
// ===================================================================

interface Props { data: GovernanceHealthData }

const DashboardVariants = ({ data }: Props) => (
  <div className="mb-4">
    <Text strong className="text-[10px] uppercase tracking-wider" style={{ color: palette.FIDESUI_MINOS }}>
      Variant A — Executive Strip
    </Text>
    <Divider className="!mb-3 !mt-1" />
    <VariantA data={data} />

    <Divider className="!my-5" />

    <Text strong className="text-[10px] uppercase tracking-wider" style={{ color: palette.FIDESUI_MINOS }}>
      Variant B — Data Wall
    </Text>
    <Divider className="!mb-3 !mt-1" />
    <VariantB data={data} />

    <Divider className="!my-5" />

    <Text strong className="text-[10px] uppercase tracking-wider" style={{ color: palette.FIDESUI_MINOS }}>
      Variant C — Donut Command Center
    </Text>
    <Divider className="!mb-3 !mt-1" />
    <VariantC data={data} />

    <Divider className="!mb-0 !mt-5" />
  </div>
);

export default DashboardVariants;
