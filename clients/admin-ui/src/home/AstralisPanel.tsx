import { antTheme, Card, Flex, Statistic, Text } from "fidesui";
import { useCallback } from "react";

import { useGetAstralisQuery } from "~/features/dashboard/dashboard.slice";

import { openDashboardDrawer } from "./useDashboardDrawer";

const METRICS = [
  {
    key: "active_conversations",
    title: "Active Conversations",
    suffix: "PIAs in progress",
  },
  {
    key: "awaiting_response",
    title: "Awaiting Response",
    suffix: "pending steward reply",
  },
  {
    key: "completed_assessments",
    title: "Completed",
    suffix: "assessments finished",
  },
  {
    key: "risks_identified",
    title: "Risks Identified",
    suffix: "across active assessments",
  },
] as const;

type MetricKey = (typeof METRICS)[number]["key"];

export const AstralisPanel = () => {
  const { token } = antTheme.useToken();
  const { data, isLoading } = useGetAstralisQuery();

  const handleMetricClick = useCallback((metric: MetricKey) => {
    openDashboardDrawer({ type: "astralis", metric });
  }, []);

  return (
    <Card
      title="Astralis Agent Activity"
      variant="borderless"
      loading={isLoading}
    >
      <Flex gap="large" wrap="wrap">
        {METRICS.map(({ key, title, suffix }) => {
          const value = data?.[key] ?? 0;
          const isOverdue = key === "awaiting_response" && value > 0;

          return (
            <Flex
              key={key}
              vertical
              gap={4}
              className="min-w-[180px] flex-1 cursor-pointer rounded-lg border border-solid border-[var(--ant-color-border)] p-4 transition-colors hover:border-[var(--ant-color-primary)]"
              onClick={() => handleMetricClick(key)}
            >
              <Flex align="center" gap={8}>
                {key === "active_conversations" && (
                  <span
                    className="inline-block size-2 animate-pulse rounded-full"
                    style={{ backgroundColor: token.colorSuccess }}
                  />
                )}
                <Statistic
                  value={value}
                  valueStyle={{
                    fontSize: token.fontSizeHeading3,
                    color: isOverdue ? token.colorWarning : undefined,
                  }}
                />
              </Flex>
              <Text strong style={isOverdue ? { color: token.colorWarning } : undefined}>
                {title}
              </Text>
              <Text type="secondary" className="text-xs">
                {suffix}
              </Text>
            </Flex>
          );
        })}
      </Flex>
    </Card>
  );
};
