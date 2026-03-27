import { antTheme, DonutChart, Flex, Text } from "fidesui";
import NextLink from "next/link";

import { ADD_SYSTEMS_MANUAL_ROUTE } from "~/features/common/nav/routes";
import { useGetSystemCoverageQuery } from "~/features/dashboard/dashboard.slice";

const BREAKDOWN_ITEMS = [
  { key: "fully_classified", label: "Fully classified", color: "colorSuccess" },
  { key: "partially_classified", label: "Partially classified", color: "colorWarning" },
  { key: "unclassified", label: "Unclassified", color: "colorBorder" },
  { key: "without_steward", label: "Without steward", color: "colorError" },
] as const;

export const SystemCoverageCard = () => {
  const { token } = antTheme.useToken();
  const { data: coverage, isLoading } = useGetSystemCoverageQuery();

  const percentage = coverage?.coverage_percentage ?? 0;

  if (isLoading) {
    return null;
  }

  return (
    <Flex vertical>
      {/* Header */}
      <Flex align="center" justify="space-between" className="mb-5">
        <Text
          type="secondary"
          style={{
            fontFamily: token.fontFamilyCode,
            fontSize: 10,
            fontWeight: 500,
            letterSpacing: "1.5px",
            textTransform: "uppercase",
          }}
        >
          System Coverage
        </Text>
        <NextLink
          href={ADD_SYSTEMS_MANUAL_ROUTE}
          passHref
          style={{
            fontSize: 12,
            fontWeight: 500,
            color: "var(--fidesui-terracotta)",
            textDecoration: "none",
          }}
        >
          Connect more &rarr;
        </NextLink>
      </Flex>

      {/* Donut + summary — centered */}
      <Flex vertical align="center" className="mb-5 text-center">
        <div className="mb-3 size-[140px]">
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
              <Flex vertical align="center">
                <Text
                  strong
                  style={{
                    fontFamily: token.fontFamilyCode,
                    fontSize: 28,
                    fontWeight: 500,
                  }}
                >
                  {percentage}%
                </Text>
                <Text
                  type="secondary"
                  className="text-[11px]"
                >
                  covered
                </Text>
              </Flex>
            }
          />
        </div>
        <Text strong className="text-[15px]">
          {coverage?.total_systems ?? 0} systems known
        </Text>
        <Text type="secondary" className="text-[13px]">
          {coverage?.fully_classified ?? 0} governed, {(coverage?.total_systems ?? 0) - (coverage?.fully_classified ?? 0)} need attention
        </Text>
      </Flex>

      {/* Breakdown */}
      <Flex vertical gap={4}>
        {BREAKDOWN_ITEMS.map(({ key, label, color }) => (
          <Flex key={key} align="center" gap={8} className="text-xs">
            <div
              className="size-[7px] shrink-0 rounded-sm"
              style={{ backgroundColor: token[color as keyof typeof token] as string }}
            />
            <Text
              strong
              style={{
                fontFamily: token.fontFamilyCode,
                minWidth: 20,
                textAlign: "right",
              }}
            >
              {coverage?.[key] ?? 0}
            </Text>
            <Text type="secondary">{label}</Text>
          </Flex>
        ))}
      </Flex>
    </Flex>
  );
};
