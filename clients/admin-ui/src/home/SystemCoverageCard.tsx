import type { AntColorTokenKey } from "fidesui";
import {
  antTheme,
  Card,
  Divider,
  DonutChart,
  Flex,
  Icons,
  Text,
  Tooltip,
} from "fidesui";

import { RouterLink } from "~/features/common/nav/RouterLink";
import { ADD_SYSTEMS_MANUAL_ROUTE } from "~/features/common/nav/routes";
import { useGetSystemCoverageQuery } from "~/features/dashboard/dashboard.slice";
import type { SystemCoverageResponse } from "~/features/dashboard/types";

const BREAKDOWN_ITEMS: {
  key: keyof SystemCoverageResponse;
  label: string;
  color: AntColorTokenKey;
}[] = [
  { key: "fully_classified", label: "Fully classified", color: "colorSuccess" },
  {
    key: "partially_classified",
    label: "Partially classified",
    color: "colorWarning",
  },
  { key: "unclassified", label: "Unclassified", color: "colorError" },
  {
    key: "without_steward",
    label: "Without steward",
    color: "colorTextQuaternary",
  },
];

export const SystemCoverageCard = () => {
  const { token } = antTheme.useToken();
  const { data: coverage, isLoading } = useGetSystemCoverageQuery();

  const percentage = coverage?.coverage_percentage ?? 0;

  return (
    <Card
      title={
        <Tooltip
          placement="bottom"
          title="What percentage of your known data systems are under active governance — connected, classified, and assigned a steward."
        >
          <Flex
            style={{ cursor: "pointer", display: "inline-flex" }}
            align="center"
            gap={4}
          >
            <Text>System Coverage</Text>
            <Icons.Help size={14} className="opacity-30" />
          </Flex>
        </Tooltip>
      }
      variant="borderless"
      loading={isLoading}
      className="h-full"
      extra={
        <RouterLink href={ADD_SYSTEMS_MANUAL_ROUTE}>
          Connect more systems
        </RouterLink>
      }
    >
      <Flex vertical gap="large" className="h-full">
        <Flex gap="large" align="start">
          <div className="size-[100px] shrink-0">
            <DonutChart
              variant="thick"
              segments={BREAKDOWN_ITEMS.map(({ key, label, color }) => ({
                value: coverage?.[key] ?? 0,
                color,
                name: label,
              }))}
              centerLabel={
                <Text strong className="text-base">
                  {percentage}%
                </Text>
              }
            />
          </div>
          <Flex vertical gap={0} className="flex-1">
            <Text strong className="mb-2 text-sm">
              {coverage?.total_systems ?? 0} systems known
            </Text>
            {BREAKDOWN_ITEMS.map(({ key, label, color }, index) => (
              <div key={key}>
                {index > 0 && <Divider className="!my-1" />}
                <Flex align="center" gap={8}>
                  <div
                    className="size-2.5 shrink-0 rounded-full"
                    style={{
                      backgroundColor: token[color],
                    }}
                  />
                  <Text strong className="text-sm">
                    {coverage?.[key] ?? 0}
                  </Text>
                  <Text type="secondary" className="text-sm">
                    {label}
                  </Text>
                </Flex>
              </div>
            ))}
          </Flex>
        </Flex>
      </Flex>
    </Card>
  );
};
