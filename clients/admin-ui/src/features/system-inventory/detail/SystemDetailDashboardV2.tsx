import { Col, Flex, Progress, Row, Statistic, Text, Title } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";

import { useCountUp } from "~/home/useCountUp";

import type { MockSystem } from "../types";
import { computeSystemDimensions } from "../utils";

interface SystemDetailDashboardV2Props {
  system: MockSystem;
}

const DIMENSION_COLORS = [
  palette.FIDESUI_TERRACOTTA,
  palette.FIDESUI_OLIVE,
  palette.FIDESUI_SANDSTONE,
  palette.FIDESUI_MINOS,
];

function computeSystemScore(system: MockSystem): number {
  const dims = computeSystemDimensions(system);
  if (dims.length === 0) return 0;
  return Math.round(dims.reduce((s: number, d) => s + d.score, 0) / dims.length);
}

const MetricCard = ({
  children,
  highlight = false,
}: {
  children: React.ReactNode;
  highlight?: boolean;
}) => (
  <div
    style={{
      backgroundColor: highlight ? palette.FIDESUI_BG_CAUTION : palette.FIDESUI_NEUTRAL_75,
    }}
    className="flex h-full w-full flex-col justify-between rounded-lg px-4 py-4"
  >
    {children}
  </div>
);

const SystemDetailDashboardV2 = ({ system }: SystemDetailDashboardV2Props) => {
  const dimensions = computeSystemDimensions(system);
  const score = computeSystemScore(system);
  const animatedScore = useCountUp(score);

  const pieData = dimensions.flatMap((dim, i) => {
    const segments = [
      { name: dim.label, value: dim.score, color: DIMENSION_COLORS[i % DIMENSION_COLORS.length] },
    ];
    if (dim.score < 100) {
      segments.push({ name: `${dim.label}-bg`, value: 100 - dim.score, color: "#e6e6e8" });
    }
    return segments;
  });

  const totalFields =
    system.classification.approved +
    system.classification.pending +
    system.classification.unreviewed;
  const classPct =
    totalFields > 0
      ? Math.round((system.classification.approved / totalFields) * 100)
      : 0;

  const totalDatasets = system.datasets.length;
  const totalFieldCount = system.datasets.reduce((sum, d) => sum + d.fieldCount, 0);
  const totalCollections = system.datasets.reduce((sum, d) => sum + d.collectionCount, 0);

  return (
    <Row gutter={[12, 12]} className="mb-4 items-stretch">
      <Col span={8} className="flex">
        <MetricCard highlight={score < 70}>
          <Text type="secondary" className="mb-2 block text-[10px] uppercase tracking-wider">
            Governance Score
          </Text>
          <Flex align="center" gap={8}>
            <div className="relative size-[72px] shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={22}
                    outerRadius={34}
                    paddingAngle={4}
                    dataKey="value"
                    startAngle={90}
                    endAngle={-270}
                    stroke="none"
                    cornerRadius={2}
                  >
                    {pieData.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex items-center justify-center" style={{ marginTop: -2 }}>
                <Statistic
                  value={animatedScore}
                  className="[&_.ant-statistic-content-value]:!text-sm [&_.ant-statistic-content-value]:!font-bold [&_.ant-statistic-content-value]:!leading-none"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-x-3 gap-y-1">
              {dimensions.map((dim, i) => (
                <Flex key={dim.label} align="center" gap={4}>
                  <div
                    className="size-[5px] shrink-0 rounded-full"
                    style={{ backgroundColor: DIMENSION_COLORS[i % DIMENSION_COLORS.length] }}
                  />
                  <Text className="whitespace-nowrap text-[10px]">
                    {dim.label} {dim.score}%
                  </Text>
                </Flex>
              ))}
            </div>
          </Flex>
        </MetricCard>
      </Col>
      <Col span={6} className="flex">
        <MetricCard>
          <Text type="secondary" className="text-[10px] uppercase tracking-wider">
            Classification
          </Text>
          <Title level={2} className="!mb-1 !mt-1">{classPct}%</Title>
          <Progress
            percent={classPct}
            showInfo={false}
            strokeColor="#5a9a68"
            size="small"
            className="!mb-0 [&_.ant-progress-inner]:!h-[4px] [&_.ant-progress-inner]:!rounded-full"
          />
        </MetricCard>
      </Col>
      <Col span={5} className="flex">
        <MetricCard>
          <Text type="secondary" className="text-[10px] uppercase tracking-wider">
            Privacy Requests
          </Text>
          <Title level={2} className="!mb-0 !mt-1">
            {system.privacyRequests.open}{" "}
            <Text type="secondary" className="text-sm font-normal">open</Text>
          </Title>
          <Text type="secondary" className="text-[10px]">
            {system.privacyRequests.closed} closed &middot; avg {system.privacyRequests.avgAccessDays}d
          </Text>
        </MetricCard>
      </Col>
      <Col span={5} className="flex">
        <MetricCard>
          <Text type="secondary" className="text-[10px] uppercase tracking-wider">
            Datasets
          </Text>
          <Title level={2} className="!mb-0 !mt-1">{totalDatasets}</Title>
          <Text type="secondary" className="text-[10px]">
            {totalFieldCount} fields across {totalCollections} collections
          </Text>
        </MetricCard>
      </Col>
    </Row>
  );
};

export default SystemDetailDashboardV2;
