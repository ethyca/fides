import { antTheme, Card, Divider, DonutChart, Flex, Text } from "fidesui";
import NextLink from "next/link";

import { ADD_SYSTEMS_MANUAL_ROUTE } from "~/features/common/nav/routes";
import { useGetSystemCoverageQuery } from "~/features/dashboard/dashboard.slice";

const BREAKDOWN_ITEMS = [
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
] as const;

export const SystemCoverageCard = () => {
  const { token } = antTheme.useToken();
  const { data: coverage, isLoading } = useGetSystemCoverageQuery();

  const percentage = coverage?.coverage_percentage ?? 0;

  return (
    <Card
      title="System Coverage"
      variant="borderless"
      loading={isLoading}
      className="h-full"
      extra={
        <NextLink href={ADD_SYSTEMS_MANUAL_ROUTE} passHref>
          Connect more systems
        </NextLink>
      }
    >
      <Flex vertical gap="large" className="h-full">
        <Flex gap="large" align="start">
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
                      backgroundColor:
                        token[color as keyof typeof token] as string,
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
