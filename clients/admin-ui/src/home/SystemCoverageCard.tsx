import { Button, Card, DonutChart, Flex, Spin, Text } from "fidesui";
import NextLink from "next/link";

import { ADD_SYSTEMS_MANUAL_ROUTE } from "~/features/common/nav/routes";
import { useGetSystemCoverageQuery } from "~/features/dashboard/dashboard.slice";

const BREAKDOWN_ITEMS = [
  { key: "fully_classified", label: "Fully classified" },
  { key: "partially_classified", label: "Partially classified" },
  { key: "unclassified", label: "Unclassified" },
  { key: "without_steward", label: "Without steward" },
] as const;

export const SystemCoverageCard = () => {
  const { data: coverage, isLoading } = useGetSystemCoverageQuery();

  const percentage = coverage?.coverage_percentage ?? 0;

  return (
    <Spin spinning={isLoading}>
      <Card title="System Coverage" variant="borderless">
        <Flex vertical gap={16} className="h-full">
          <Flex gap={16} align="start">
            <div className="size-[100px] shrink-0">
              <DonutChart
                variant="thick"
                segments={[
                  {
                    value: coverage?.fully_classified ?? 0,
                    color: "colorSuccess",
                    name: "Fully classified",
                  },
                  {
                    value: coverage?.partially_classified ?? 0,
                    color: "colorWarning",
                    name: "Partially classified",
                  },
                  {
                    value: coverage?.unclassified ?? 0,
                    color: "colorBorder",
                    name: "Unclassified",
                  },
                ]}
                centerLabel={
                  <Text strong className="text-base">
                    {percentage}%
                  </Text>
                }
              />
            </div>
            <Flex vertical gap={4}>
              <Text strong>{coverage?.total_systems ?? 0} systems known</Text>
              {BREAKDOWN_ITEMS.map(({ key, label }) => (
                <Text key={key} type="secondary">
                  {coverage?.[key] ?? 0} {label}
                </Text>
              ))}
            </Flex>
          </Flex>
          <NextLink href={ADD_SYSTEMS_MANUAL_ROUTE} passHref>
            <Button type="default" block>
              + Connect More Systems
            </Button>
          </NextLink>
        </Flex>
      </Card>
    </Spin>
  );
};
