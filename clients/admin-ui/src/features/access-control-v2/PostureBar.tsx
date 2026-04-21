import { Information } from "@carbon/icons-react";
import { Flex, Popover, Statistic, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";

export interface InferredPurpose {
  name: string;
  queryCount: number;
}

interface PostureBarProps {
  accessHealthScore: number;
  compliantQueries: number;
  violationCount: number;
  gapCount: number;
  unknownCount: number;
  consumerCount: number;
  policyCount: number;
  violationRate: number;
  totalQueries: number;
  systemsMonitored: number;
  topInferredPurposes: InferredPurpose[];
  onUnknownClick?: () => void;
}

const PostureBar = ({
  accessHealthScore,
  compliantQueries,
  violationCount,
  gapCount,
  unknownCount,
  consumerCount,
  policyCount,
  violationRate,
  totalQueries,
  systemsMonitored,
  topInferredPurposes,
  onUnknownClick,
}: PostureBarProps) => {
  const stats = [
    {
      label: "Passing",
      value: compliantQueries,
      color: palette.FIDESUI_SUCCESS,
    },
    {
      label: "Violations",
      value: violationCount,
      color: palette.FIDESUI_ERROR,
    },
    {
      label: "Gaps",
      value: gapCount,
      color: palette.FIDESUI_WARNING,
    },
    {
      label: "Unknown identities",
      value: unknownCount,
      color: palette.FIDESUI_MINOS,
      onClick: onUnknownClick,
    },
  ];

  const popoverContent = (
    <Flex vertical gap={8} className="max-w-[300px]">
      <Text strong className="text-xs">
        How is access health calculated?
      </Text>
      <Text type="secondary" className="text-xs">
        Access health reflects the percentage of observed data access that is
        governed by a declared policy and performed by a registered consumer.
      </Text>
      {[
        {
          label: "Passing",
          color: palette.FIDESUI_SUCCESS,
          desc: "Queries made by registered consumers within an approved policy boundary.",
        },
        {
          label: "Violations",
          color: palette.FIDESUI_ERROR,
          desc: "Queries by registered consumers that fall outside their approved policy boundary.",
        },
        {
          label: "Gaps",
          color: palette.FIDESUI_WARNING,
          desc: "Data being accessed with no matching policy at all — ungoverned access.",
        },
        {
          label: "Unknown identities",
          color: palette.FIDESUI_MINOS,
          desc: "Query sources not registered as consumers. Findings may be incomplete until resolved.",
        },
      ].map((item) => (
        <Flex key={item.label} vertical gap={2}>
          <Flex align="center" gap={6}>
            <div
              className="size-2 shrink-0 rounded-full"
              style={{ backgroundColor: item.color }}
            />
            <Text className="text-xs">{item.label}</Text>
          </Flex>
          <Text type="secondary" className="pl-4 text-[10px]">
            {item.desc}
          </Text>
        </Flex>
      ))}
      <Text type="secondary" className="text-xs">
        Score = passing / (passing + violations + gaps + unknown) ={" "}
        {accessHealthScore}
      </Text>
    </Flex>
  );

  return (
    <Flex gap={32} align="stretch" className="py-2">
      {/* Left: donut score */}
      <Flex vertical gap={12} className="shrink-0">
        <Flex align="center" gap={4}>
          <Text strong className="text-[10px] uppercase tracking-wider">
            Access health
          </Text>
          <Popover
            content={popoverContent}
            trigger="hover"
            placement="bottomLeft"
          >
            <Information
              size={12}
              className="cursor-help"
              style={{ color: palette.FIDESUI_NEUTRAL_500 }}
            />
          </Popover>
        </Flex>
        <Flex align="center" gap={16}>
            <div className="relative size-[140px] shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats.map((s) => ({
                      name: s.label,
                      value: s.value,
                      color: s.color,
                    }))}
                    cx="50%"
                    cy="50%"
                    innerRadius={48}
                    outerRadius={64}
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
                    {stats.map((s) => (
                      <Cell key={s.label} fill={s.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex items-center justify-center">
                <Flex vertical align="center" gap={0}>
                  <Statistic
                    value={accessHealthScore}
                    className="[&_.ant-statistic-content-value]:!text-xl [&_.ant-statistic-content-value]:!font-bold"
                  />
                  <Text type="secondary" className="-mt-1 text-[9px]">
                    / 100
                  </Text>
                </Flex>
              </div>
            </div>
            <Flex vertical gap={6}>
              {stats.map((s) => (
                <Flex key={s.label} align="center" gap={8}>
                  <div
                    className="size-2 shrink-0 rounded-full"
                    style={{ backgroundColor: s.color }}
                  />
                  <Text
                    className="text-xs"
                    style={{ color: palette.FIDESUI_MINOS }}
                  >
                    {s.label} ({s.value})
                  </Text>
                </Flex>
              ))}
            </Flex>
          </Flex>
      </Flex>

      {/* Middle: key metrics */}
      <Flex
        vertical
        gap={12}
        className="border-l border-solid pl-8"
        style={{ borderColor: palette.FIDESUI_NEUTRAL_100 }}
      >
        <Text
          strong
          className="block text-[10px] uppercase tracking-wider"
        >
          Overview
        </Text>
        <Flex vertical gap={16}>
          <Flex gap={32}>
            <Flex vertical gap={2}>
              <Text strong className="text-lg">
                {consumerCount}
              </Text>
              <Text type="secondary" className="text-[10px]">
                Consumers
              </Text>
            </Flex>
            <Flex vertical gap={2}>
              <Text strong className="text-lg">
                {policyCount}
              </Text>
              <Text type="secondary" className="text-[10px]">
                Access policies
              </Text>
            </Flex>
            <Flex vertical gap={2}>
              <Text
                strong
                className="text-lg"
                style={
                  violationRate > 10
                    ? { color: palette.FIDESUI_ERROR }
                    : undefined
                }
              >
                {violationRate}%
              </Text>
              <Text type="secondary" className="text-[10px]">
                Violation rate
              </Text>
            </Flex>
          </Flex>
          <Flex gap={32}>
            <Flex vertical gap={2}>
              <Text strong className="text-lg">
                {totalQueries.toLocaleString()}
              </Text>
              <Text type="secondary" className="text-[10px]">
                Queries detected
              </Text>
            </Flex>
            <Flex vertical gap={2}>
              <Text strong className="text-lg">
                {systemsMonitored}
              </Text>
              <Text type="secondary" className="text-[10px]">
                Systems monitored
              </Text>
            </Flex>
          </Flex>
        </Flex>
      </Flex>

      {/* Right: top inferred purposes */}
      <div
        className="min-w-0 flex-1 border-l border-solid pl-8"
        style={{ borderColor: palette.FIDESUI_NEUTRAL_100 }}
      >
        <Text
          strong
          className="mb-4 block text-[10px] uppercase tracking-wider"
        >
          Top inferred purposes
        </Text>
        <Flex vertical gap={0}>
          {topInferredPurposes.map((p) => (
            <Flex
              key={p.name}
              justify="space-between"
              align="center"
              className="border-b border-solid py-1.5 last:border-b-0"
              style={{ borderColor: palette.FIDESUI_NEUTRAL_75 }}
            >
              <Text className="text-[11px]">{p.name}</Text>
              <Text type="secondary" className="text-[11px]">
                {p.queryCount.toLocaleString()} queries
              </Text>
            </Flex>
          ))}
        </Flex>
      </div>
    </Flex>
  );
};

export default PostureBar;
