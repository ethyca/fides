import { antTheme, Divider, Flex, Text } from "fidesui";
import { useMemo } from "react";

import type { DataPurpose, PurposeSummary } from "./data-purpose.slice";
import { formatDataUse, getCompleteness } from "./purposeUtils";

// fidesui palette — info blue, matching SchemaExplorerDashboard
const PALETTE_INFO = "#4a90e2";

interface PurposeSummaryRowProps {
  purposes: DataPurpose[];
  summaries: PurposeSummary[];
}

const PurposeSummaryRow = ({ purposes, summaries }: PurposeSummaryRowProps) => {
  const { token } = antTheme.useToken();

  const totalSystems = useMemo(
    () => summaries.reduce((sum, s) => sum + s.system_count, 0),
    [summaries],
  );

  const totalDatasets = useMemo(
    () => summaries.reduce((sum, s) => sum + s.dataset_count, 0),
    [summaries],
  );

  const completeCount = useMemo(
    () => purposes.filter((p) => getCompleteness(p) >= 80).length,
    [purposes],
  );

  const inProgressCount = useMemo(
    () =>
      purposes.filter((p) => {
        const c = getCompleteness(p);
        return c > 0 && c < 80;
      }).length,
    [purposes],
  );

  const emptyCount = purposes.length - completeCount - inProgressCount;

  const completePct =
    purposes.length > 0 ? (completeCount / purposes.length) * 100 : 0;
  const inProgressPct =
    purposes.length > 0 ? (inProgressCount / purposes.length) * 100 : 0;
  const emptyPct =
    purposes.length > 0 ? (emptyCount / purposes.length) * 100 : 0;

  const categoryBreakdownText = useMemo(() => {
    const counts: Record<string, number> = {};
    purposes.forEach((p) => {
      const label = formatDataUse(p.data_use);
      counts[label] = (counts[label] || 0) + 1;
    });
    return Object.entries(counts)
      .sort(([, a], [, b]) => b - a)
      .map(([label, count]) => `${count} ${label.toLowerCase()}`)
      .join(", ");
  }, [purposes]);

  return (
    <Flex className="w-full py-2" align="stretch">
      {/* Section 1: Completeness overview */}
      <Flex vertical gap={6} className="min-w-0 flex-1 pr-4">
        <Flex vertical>
          <Text
            strong
            className="text-2xl leading-none"
            style={{ fontVariantNumeric: "tabular-nums" }}
          >
            {purposes.length}
          </Text>
          <Text type="secondary" className="mt-0.5 text-xs">
            purposes
          </Text>
        </Flex>

        {/* Stacked progress bar */}
        <div className="flex h-2 w-full overflow-hidden rounded-sm bg-gray-100">
          <div
            className="transition-all duration-1000 ease-in-out"
            style={{
              width: `${completePct}%`,
              backgroundColor: token.colorSuccess,
            }}
          />
          <div
            className="transition-all duration-1000 ease-in-out"
            style={{
              width: `${inProgressPct}%`,
              backgroundColor: PALETTE_INFO,
            }}
          />
          <div
            className="transition-all duration-1000 ease-in-out"
            style={{
              width: `${emptyPct}%`,
              backgroundColor: token.colorTextQuaternary,
            }}
          />
        </div>

        {/* Legend */}
        <Flex gap="middle">
          <Flex align="center" gap={6}>
            <div
              className="size-2 flex-none rounded-full"
              style={{ backgroundColor: token.colorSuccess }}
            />
            <Text className="text-xs">{completeCount} complete</Text>
          </Flex>
          <Flex align="center" gap={6}>
            <div
              className="size-2 flex-none rounded-full"
              style={{ backgroundColor: PALETTE_INFO }}
            />
            <Text className="text-xs">{inProgressCount} in progress</Text>
          </Flex>
          <Flex align="center" gap={6}>
            <div
              className="size-2 flex-none rounded-full"
              style={{ backgroundColor: token.colorTextQuaternary }}
            />
            <Text className="text-xs">{emptyCount} not started</Text>
          </Flex>
        </Flex>
      </Flex>

      <Divider type="vertical" className="!mx-0 !h-auto self-stretch" />

      {/* Section 2: Coverage */}
      <div className="min-w-0 flex-1 px-4">
        <Text strong className="mb-2 block text-xs">
          Coverage
        </Text>
        <div className="mb-1">
          <Text type="secondary" className="text-xs">
            Data consumers:{" "}
          </Text>
          <Text className="text-xs">{totalSystems}</Text>
        </div>
        <div>
          <Text type="secondary" className="text-xs">
            Datasets:{" "}
          </Text>
          <Text className="text-xs">{totalDatasets}</Text>
        </div>
      </div>

      <Divider type="vertical" className="!mx-0 !h-auto self-stretch" />

      {/* Section 3: Categories */}
      <div className="min-w-0 flex-1 pl-4">
        <Text strong className="mb-2 block text-xs">
          By category
        </Text>
        <div className="truncate">
          <Text type="secondary" className="text-xs">
            {categoryBreakdownText || "None"}
          </Text>
        </div>
      </div>
    </Flex>
  );
};

export default PurposeSummaryRow;
