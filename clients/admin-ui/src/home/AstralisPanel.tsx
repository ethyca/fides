import {
  antTheme,
  Card,
  CUSTOM_TAG_COLOR,
  Flex,
  Statistic,
  Tag,
  Text,
} from "fidesui";
import { useCallback } from "react";

import { useGetAstralisQuery } from "~/features/dashboard/dashboard.slice";

import { openDashboardDrawer } from "./useDashboardDrawer";

const METRICS = [
  { key: "active_conversations", label: "Active" },
  { key: "awaiting_response", label: "Awaiting" },
  { key: "completed_assessments", label: "Completed" },
  { key: "risks_identified", label: "Risks" },
] as const;

type MetricKey = (typeof METRICS)[number]["key"];

const STATUS_TAG: Record<
  string,
  { color: CUSTOM_TAG_COLOR; label: string }
> = {
  in_progress: { color: CUSTOM_TAG_COLOR.INFO, label: "In Progress" },
  awaiting: { color: CUSTOM_TAG_COLOR.WARNING, label: "Awaiting" },
  completed: { color: CUSTOM_TAG_COLOR.SUCCESS, label: "Completed" },
};

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
      className="flex h-full flex-col [&_.ant-card-body]:flex-1 [&_.ant-card-body]:overflow-hidden"
    >
      <Flex vertical className="h-full">
        {/* Compact 2x2 metric grid */}
        <Flex wrap="wrap" gap={8} className="mb-3 shrink-0">
          {METRICS.map(({ key, label }) => {
            const value = data?.[key] ?? 0;
            const isActive = key === "active_conversations";
            const isOverdue = key === "awaiting_response" && value > 0;

            return (
              <Flex
                key={key}
                align="center"
                gap={6}
                className="min-w-[calc(50%-4px)] flex-1 cursor-pointer rounded-md border border-solid border-[var(--ant-color-border)] px-3 py-2 transition-colors hover:border-[var(--ant-color-primary)]"
                onClick={() => handleMetricClick(key)}
              >
                {isActive && (
                  <span
                    className="inline-block size-1.5 animate-pulse rounded-full"
                    style={{ backgroundColor: token.colorSuccess }}
                  />
                )}
                <Statistic
                  value={value}
                  valueStyle={{
                    fontSize: token.fontSizeLG,
                    color: isOverdue ? token.colorWarning : undefined,
                  }}
                />
                <Text
                  type="secondary"
                  className="text-xs"
                  style={isOverdue ? { color: token.colorWarning } : undefined}
                >
                  {label}
                </Text>
              </Flex>
            );
          })}
        </Flex>

        {/* Scrollable conversation list */}
        <Flex vertical gap={0} className="min-h-0 flex-1 overflow-y-auto">
          {data?.conversations?.map((conv) => {
            const tag = STATUS_TAG[conv.status];
            const isOverdue =
              conv.status === "awaiting" && conv.days_in_status > 3;

            return (
              <Flex
                key={`${conv.steward_name}-${conv.system_name}`}
                justify="space-between"
                align="center"
                className="border-b border-solid border-b-[var(--ant-color-border)] py-2"
              >
                <Flex vertical gap={0}>
                  <Text strong className="text-xs">
                    {conv.steward_name}
                  </Text>
                  <Text type="secondary" className="text-[11px]">
                    {conv.system_name}
                  </Text>
                </Flex>
                <Flex align="center" gap={6}>
                  {isOverdue && (
                    <Text type="danger" className="text-[11px]">
                      {conv.days_in_status}d overdue
                    </Text>
                  )}
                  <Tag color={tag.color} className="!mr-0 !text-[11px]">
                    {tag.label}
                  </Tag>
                </Flex>
              </Flex>
            );
          })}
        </Flex>
      </Flex>
    </Card>
  );
};
