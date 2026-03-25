import { Card, Flex, Progress, Typography } from "fidesui";
import { theme } from "antd/lib";
import { useId, useMemo } from "react";
import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart as RechartsRadarChart,
  ResponsiveContainer,
} from "recharts";

import type { GovernanceData } from "../types";

const { Text } = Typography;

// ── Design tokens ──

const STATUS_COLORS_MAP = {
  success: "#5a9a68",
  warning: "#e59d47",
  error: "#d9534f",
};

// ── Tick renderer ──

interface RadarTickProps {
  x?: number;
  y?: number;
  payload?: { value: string; index: number };
  data: GovernanceData["dimensions"];
  textColor: string;
  monoFont: string;
}

const RadarTick = ({
  x = 0,
  y = 0,
  payload,
  data,
  textColor,
  monoFont,
}: RadarTickProps) => {
  if (!payload) return null;
  const lines = payload.value.split("\n");
  const point = data[payload.index];
  const statusColor = point?.status
    ? STATUS_COLORS_MAP[point.status]
    : undefined;

  return (
    <g>
      <text
        x={x}
        y={y}
        textAnchor="middle"
        dominantBaseline="central"
        fill={textColor}
        fillOpacity={0.7}
        fontSize={10}
        fontWeight={500}
        letterSpacing="-0.03em"
      >
        {lines.map((line, i) => (
          <tspan key={line} x={x} dy={i === 0 ? 0 : 12}>
            {line}
          </tspan>
        ))}
      </text>
      {point && (
        <text
          x={x}
          y={y + lines.length * 12 + 2}
          textAnchor="middle"
          dominantBaseline="hanging"
          fill={statusColor ?? textColor}
          fontSize={10}
          fontWeight={700}
          fontFamily={monoFont}
        >
          {point.value}
          {point.previous != null && (
            <tspan fill={textColor} opacity={0.35} fontWeight={400}>
              {" "}
              / {point.previous}
            </tspan>
          )}
        </text>
      )}
    </g>
  );
};

// ── Custom dual-layer radar chart ──

const CustomRadar = ({ data }: { data: GovernanceData["dimensions"] }) => {
  const { token } = theme.useToken();
  const uid = useId();
  const gradientId = `gov-fill-${uid}`;
  const prevGradientId = `gov-prev-${uid}`;
  const glowId = `gov-glow-${uid}`;
  const bloomId = `gov-bloom-${uid}`;
  const chartColor = token.colorText;

  const chartData = useMemo(
    () =>
      data.map((d) => ({
        ...d,
        prev: d.previous ?? 0,
      })),
    [data],
  );

  return (
    <div className="w-full h-full pointer-events-none">
      <ResponsiveContainer width="100%" height="100%">
        <RechartsRadarChart
          data={chartData}
          cx="50%"
          cy="46%"
          outerRadius="62%"
        >
          <defs>
            <radialGradient id={gradientId} cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor={chartColor} stopOpacity={0} />
              <stop offset="60%" stopColor={chartColor} stopOpacity={0.06} />
              <stop offset="100%" stopColor={chartColor} stopOpacity={0.18} />
            </radialGradient>

            <radialGradient id={prevGradientId} cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor={chartColor} stopOpacity={0} />
              <stop offset="100%" stopColor={chartColor} stopOpacity={0.06} />
            </radialGradient>

            <filter id={glowId} x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="inner" />
              <feColorMatrix in="inner" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.25 0" result="innerColor" />
              <feMerge>
                <feMergeNode in="innerColor" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            <filter id={bloomId} x="-80%" y="-80%" width="260%" height="260%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="16" result="bloom" />
              <feColorMatrix in="bloom" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.12 0" result="bloomColor" />
              <feMerge>
                <feMergeNode in="bloomColor" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          <PolarGrid stroke={chartColor} strokeWidth={0.4} strokeOpacity={0.15} />
          <PolarRadiusAxis tick={false} axisLine={false} domain={[0, 100]} />

          <Radar
            dataKey="prev"
            stroke={chartColor}
            strokeWidth={1}
            strokeOpacity={0.25}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeDasharray="4 3"
            fill={`url(#${prevGradientId})`}
            dot={false}
            activeDot={false}
            isAnimationActive
            animationDuration={800}
            animationEasing="ease-in-out"
          />

          <Radar
            dataKey="value"
            stroke={chartColor}
            strokeWidth={1.2}
            strokeOpacity={0.6}
            strokeLinecap="round"
            strokeLinejoin="round"
            fill={`url(#${gradientId})`}
            style={{ filter: `url(#${bloomId})` }}
            dot={(props: { cx?: number; cy?: number; index?: number }) => {
              const { cx: dotCx = 0, cy: dotCy = 0, index: idx = 0 } = props;
              const point = data[idx];
              const fill = point?.status
                ? STATUS_COLORS_MAP[point.status]
                : chartColor;
              return (
                <g key={idx} style={{ filter: `url(#${glowId})` }}>
                  <circle cx={dotCx} cy={dotCy} r={6} fill={fill} fillOpacity={0.15} />
                  <circle cx={dotCx} cy={dotCy} r={3} fill={fill} stroke={token.colorBgContainer} strokeWidth={1.5} />
                </g>
              );
            }}
            activeDot={false}
            isAnimationActive
            animationDuration={600}
            animationEasing="ease-in-out"
          />

          <PolarAngleAxis
            dataKey="subject"
            tick={<RadarTick data={data} textColor={chartColor} monoFont={token.fontFamilyCode} />}
          />
        </RechartsRadarChart>
      </ResponsiveContainer>
    </div>
  );
};

// ── Main component ──

interface GovernancePostureProps {
  data: GovernanceData;
  variant?: "radar" | "circle";
}

const GovernancePosture = ({
  data,
  variant = "radar",
}: GovernancePostureProps) => {
  const { token } = theme.useToken();
  const trendColor = data.trend >= 0 ? token.colorSuccess : token.colorError;
  const trendSign = data.trend >= 0 ? "+" : "";

  if (variant === "circle") {
    return (
      <Card className="rounded-lg h-full" styles={{ body: { padding: "14px 20px" } }}>
        <Text className="text-[10px] tracking-[0.1em] mb-3 block" type="secondary" strong>
          GOVERNANCE POSTURE
        </Text>
        <Flex vertical align="center" gap={8}>
          <Progress
            type="circle"
            percent={data.score}
            size={60}
            strokeWidth={8}
            strokeColor={token.colorSuccess}
            strokeLinecap="square"
            format={(pct) => (
              <span className="text-[16px] font-bold" style={{ fontFamily: token.fontFamilyCode }}>{pct}</span>
            )}
          />
          <Text className="text-[11px] font-semibold" style={{ color: trendColor, fontFamily: token.fontFamilyCode }}>
            {trendSign}{data.trend} vs last mo
          </Text>
          <Text type="secondary" className="text-[10px]">
            Your privacy posture is strong.
          </Text>
        </Flex>
      </Card>
    );
  }

  return (
    <Card className="rounded-lg h-full" styles={{ body: { padding: "18px 20px" } }}>
      <Text className="text-[10px] tracking-[0.1em] mb-2 block" type="secondary" strong>
        GOVERNANCE POSTURE
      </Text>

      <Flex align="baseline" gap={6} className="mb-2">
        <Text className="text-[32px] font-bold leading-none" style={{ fontFamily: token.fontFamilyCode }}>{data.score}</Text>
        <Text className="text-[12px] font-semibold" style={{ color: trendColor, fontFamily: token.fontFamilyCode }}>
          {trendSign}{data.trend}
        </Text>
      </Flex>

      <div className="h-[300px] w-full">
        <CustomRadar data={data.dimensions} />
      </div>

      <div className="pt-2" style={{ borderTop: `1px solid ${token.colorBorder}` }}>
        <Text type="secondary" className="text-[11px] leading-relaxed">
          Your posture score improved by {data.trend} points. Your privacy
          posture is strong. Keep monitoring for changes.
        </Text>
      </div>
    </Card>
  );
};

export default GovernancePosture;
