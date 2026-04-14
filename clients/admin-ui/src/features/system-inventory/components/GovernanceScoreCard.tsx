import { Information } from "@carbon/icons-react";
import { Flex, Popover, Statistic, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";

import { useCountUp } from "~/home/useCountUp";

import { PILLAR_CONFIG } from "../constants";
import type { GovernanceHealthData } from "../types";

interface GovernanceScoreCardProps {
  data: GovernanceHealthData;
}

const ScorePopoverContent = ({ data }: { data: GovernanceHealthData }) => (
  <Flex vertical gap={8} className="max-w-[280px]">
    <Text strong className="text-xs">
      How is this score calculated?
    </Text>
    <Text type="secondary" className="text-xs">
      The inventory health score is the average of three governance pillars,
      each measured 0–100 across all registered systems:
    </Text>
    {data.dimensions.map((dim) => (
      <Flex key={dim.key} vertical gap={2}>
        <Flex justify="space-between" align="center">
          <Flex align="center" gap={6}>
            <div
              className="size-2 shrink-0 rounded-full"
              style={{ backgroundColor: dim.color }}
            />
            <Text className="text-xs">{dim.label}</Text>
          </Flex>
          <Text strong className="text-xs">
            {dim.score}%
          </Text>
        </Flex>
        <Text type="secondary" className="pl-4 text-[10px]">
          {PILLAR_CONFIG[dim.key].description}
        </Text>
      </Flex>
    ))}
    <Text type="secondary" className="text-xs">
      Score = ({data.dimensions.map((d) => d.score).join(" + ")}) /{" "}
      {data.dimensions.length} = {data.score}
    </Text>
  </Flex>
);

const GovernanceScoreCard = ({ data }: GovernanceScoreCardProps) => {
  const animatedScore = useCountUp(data.score);
  const totalSystems =
    data.healthBreakdown.healthy + data.healthBreakdown.issues;

  // Each pillar gets an equal slice of the donut. Within its slice, the
  // colored fill represents the score (0–100) and the rest is neutral.
  const pieData = data.dimensions.flatMap((dim) => [
    {
      name: dim.label,
      value: dim.score,
      color: dim.color,
    },
    {
      name: `${dim.label}-bg`,
      value: 100 - dim.score,
      color: palette.FIDESUI_NEUTRAL_100,
    },
  ]);

  return (
    <Flex vertical gap={8}>
      {/* Header row */}
      <Flex align="center" gap={4}>
        <Text strong className="text-[10px] uppercase tracking-wider">
          Inventory health
        </Text>
        <Popover
          content={<ScorePopoverContent data={data} />}
          trigger="hover"
          placement="bottomLeft"
        >
          <Information
            size={12}
            className="cursor-help"
            style={{ color: palette.FIDESUI_NEUTRAL_500 }}
          />
        </Popover>
        <Text type="secondary" className="ml-auto text-[10px]">
          {totalSystems} systems &middot; {data.totalRiskScore} risks
        </Text>
      </Flex>

      {/* Donut + legend */}
      <Flex align="center" gap={16} className="mt-3">
        <div className="relative size-[160px] shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={74}
                paddingAngle={3}
                dataKey="value"
                startAngle={90}
                endAngle={-270}
                stroke="none"
                cornerRadius={3}
                isAnimationActive
                animationDuration={600}
                animationEasing="ease-in-out"
              >
                {pieData.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex items-center justify-center">
            <Flex vertical align="center" gap={0}>
              <Statistic
                value={animatedScore}
                className="[&_.ant-statistic-content-value]:!text-xl [&_.ant-statistic-content-value]:!font-bold"
              />
              <Text type="secondary" className="-mt-1 text-[9px]">
                / 100
              </Text>
            </Flex>
          </div>
        </div>

        <Flex vertical gap={6}>
          {data.dimensions.map((dim) => (
            <Flex key={dim.key} align="center" gap={8}>
              <div
                className="size-2 shrink-0 rounded-full"
                style={{ backgroundColor: dim.color }}
              />
              <Text
                className="text-xs"
                style={{ color: palette.FIDESUI_MINOS }}
              >
                {dim.label} {dim.score}%
              </Text>
            </Flex>
          ))}
        </Flex>
      </Flex>
    </Flex>
  );
};

export default GovernanceScoreCard;
