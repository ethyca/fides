import type { CarbonIconType } from "@carbon/icons-react";
import {
  Activity,
  DataBase,
  Locked,
  SettingsCheck,
} from "@carbon/icons-react";
import { Flex, Statistic, Tag, Text, Title } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";

import { useCountUp } from "~/home/useCountUp";

import type { MockSystem } from "../types";
import { SystemCapability } from "../types";
import { computeSystemDimensions, getSystemCapabilities } from "../utils";

interface SystemDetailDashboardV2Props {
  system: MockSystem;
}

const CAPABILITY_ICONS: Partial<Record<SystemCapability, CarbonIconType>> = {
  [SystemCapability.DSAR]: Locked,
  [SystemCapability.MONITORING]: Activity,
  [SystemCapability.INTEGRATIONS]: SettingsCheck,
  [SystemCapability.CLASSIFICATION]: DataBase,
};

function computeSystemScore(system: MockSystem): number {
  const dims = computeSystemDimensions(system);
  if (dims.length === 0) {
    return 0;
  }
  return Math.round(
    dims.reduce((s: number, d) => s + d.score, 0) / dims.length,
  );
}

const SystemDetailDashboardV2 = ({ system }: SystemDetailDashboardV2Props) => {
  const dimensions = computeSystemDimensions(system);
  const score = computeSystemScore(system);
  const animatedScore = useCountUp(score);
  const capabilities = getSystemCapabilities(system);

  const pieData = dimensions.flatMap((dim) => {
    const segments = [
      {
        name: dim.label,
        value: dim.score,
        color: dim.color,
      },
    ];
    if (dim.score < 100) {
      segments.push({
        name: `${dim.label}-bg`,
        value: 100 - dim.score,
        color: palette.FIDESUI_NEUTRAL_100,
      });
    }
    return segments;
  });

  const totalDatasets = system.datasets.length;
  const totalFieldCount = system.datasets.reduce(
    (sum, d) => sum + d.fieldCount,
    0,
  );
  const totalCollections = system.datasets.reduce(
    (sum, d) => sum + d.collectionCount,
    0,
  );

  return (
    <div className="mb-4">
      <Flex gap={32}>
        {/* System Health */}
        <div className="min-w-0 flex-1">
          <Text
            type="secondary"
            className="mb-2 block text-[10px] uppercase tracking-wider"
          >
            System health
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
              <div
                className="absolute inset-0 flex items-center justify-center"
                style={{ marginTop: -2 }}
              >
                <Statistic
                  value={animatedScore}
                  className="[&_.ant-statistic-content-value]:!text-sm [&_.ant-statistic-content-value]:!font-bold [&_.ant-statistic-content-value]:!leading-none"
                />
              </div>
            </div>
            <div className="grid grid-cols-1 gap-x-3 gap-y-1">
              {dimensions.map((dim) => (
                <Flex key={dim.key} align="center" gap={4}>
                  <div
                    className="size-[5px] shrink-0 rounded-full"
                    style={{ backgroundColor: dim.color }}
                  />
                  <Text className="whitespace-nowrap text-[10px]">
                    {dim.label} {dim.numerator.toLocaleString()}/
                    {dim.denominator.toLocaleString()}
                  </Text>
                </Flex>
              ))}
            </div>
          </Flex>
        </div>

        {/* Capabilities */}
        <div
          className="min-w-0 flex-1 border-l border-solid pl-8"
          style={{ borderColor: palette.FIDESUI_NEUTRAL_100 }}
        >
          <Text
            type="secondary"
            className="mb-2 block text-[10px] uppercase tracking-wider"
          >
            Capabilities
          </Text>
          {capabilities.length > 0 ? (
            <Flex gap={6} wrap className="mt-1">
              {capabilities.map((cap) => {
                const Icon = CAPABILITY_ICONS[cap];
                if (!Icon) return null;
                return (
                  <Tag
                    key={cap}
                    bordered={false}
                    style={{
                      backgroundColor: palette.FIDESUI_BG_DEFAULT,
                    }}
                  >
                    <Flex align="center" gap={4}>
                      <Icon size={12} />
                      <span className="text-xs">{cap}</span>
                    </Flex>
                  </Tag>
                );
              })}
            </Flex>
          ) : (
            <Text type="secondary" className="mt-1 text-xs">
              No capabilities detected
            </Text>
          )}
          <Text type="secondary" className="mt-2 text-[9px]">
            Based on active integrations
          </Text>
        </div>

        {/* Privacy Requests */}
        <div
          className="min-w-0 flex-1 border-l border-solid pl-8"
          style={{ borderColor: palette.FIDESUI_NEUTRAL_100 }}
        >
          <Text
            type="secondary"
            className="text-[10px] uppercase tracking-wider"
          >
            Privacy requests
          </Text>
          <Title level={3} className="!mb-0 !mt-1">
            {system.privacyRequests.open}{" "}
            <Text type="secondary" className="text-sm font-normal">
              open
            </Text>
          </Title>
          <Text type="secondary" className="text-[10px]">
            {system.privacyRequests.closed.toLocaleString()} closed &middot; avg{" "}
            {system.privacyRequests.avgAccessDays}d
          </Text>
        </div>

        {/* Datasets */}
        <div
          className="min-w-0 flex-1 border-l border-solid pl-8"
          style={{ borderColor: palette.FIDESUI_NEUTRAL_100 }}
        >
          <Text
            type="secondary"
            className="text-[10px] uppercase tracking-wider"
          >
            Datasets
          </Text>
          <Title level={3} className="!mb-0 !mt-1">
            {totalDatasets}
          </Title>
          <Text type="secondary" className="text-[10px]">
            {totalFieldCount.toLocaleString()} fields across {totalCollections}{" "}
            collections
          </Text>
        </div>
      </Flex>
    </div>
  );
};

export default SystemDetailDashboardV2;
