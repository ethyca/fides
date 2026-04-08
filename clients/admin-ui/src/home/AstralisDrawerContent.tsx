import { antTheme, Flex, Tag, Text } from "fidesui";
import { useMemo } from "react";

import {
  ASTRALIS_METRICS,
  ASTRALIS_STATUS_TAG,
  type AstralisMetricKey,
} from "~/features/dashboard/constants";
import { useGetAstralisQuery } from "~/features/dashboard/dashboard.slice";
import type { AstralisConversation } from "~/features/dashboard/types";

import { useDashboardDrawer } from "./useDashboardDrawer";

const METRIC_TO_STATUSES: Record<
  AstralisMetricKey,
  AstralisConversation["status"][] | null
> = {
  active_conversations: ["in_progress"],
  awaiting_response: ["awaiting"],
  completed_assessments: ["completed"],
  risks_identified: null, // no status filter — shows all
};

export const AstralisDrawerContent = () => {
  const { token } = antTheme.useToken();
  const { data } = useGetAstralisQuery();
  const drawer = useDashboardDrawer();
  const metric = drawer?.type === "astralis" ? drawer.metric : undefined;

  const conversations = useMemo(() => {
    const all = data?.conversations ?? [];
    if (!metric) {
      return all;
    }
    const statuses = METRIC_TO_STATUSES[metric];
    if (!statuses) {
      return all;
    }
    return all.filter((c) => statuses.includes(c.status));
  }, [data?.conversations, metric]);

  return (
    <Flex vertical gap="middle">
      {metric && (
        <Text type="secondary" className="text-xs uppercase tracking-wide">
          Filtered by:{" "}
          {ASTRALIS_METRICS.find((m) => m.key === metric)?.label ??
            metric.replace(/_/g, " ")}
        </Text>
      )}

      <Flex gap="middle" wrap="wrap" className="mb-2">
        <Flex vertical align="center" className="min-w-[80px]">
          <Text strong className="text-lg">
            {data?.active_conversations ?? 0}
          </Text>
          <Text type="secondary" className="text-xs">
            Active
          </Text>
        </Flex>
        <Flex vertical align="center" className="min-w-[80px]">
          <Text strong className="text-lg">
            {data?.completed_assessments ?? 0}
          </Text>
          <Text type="secondary" className="text-xs">
            Completed
          </Text>
        </Flex>
        <Flex vertical align="center" className="min-w-[80px]">
          <Text
            strong
            className="text-lg"
            style={
              (data?.awaiting_response ?? 0) > 0
                ? { color: token.colorWarning }
                : undefined
            }
          >
            {data?.awaiting_response ?? 0}
          </Text>
          <Text type="secondary" className="text-xs">
            Awaiting
          </Text>
        </Flex>
        <Flex vertical align="center" className="min-w-[80px]">
          <Text strong className="text-lg">
            {data?.risks_identified ?? 0}
          </Text>
          <Text type="secondary" className="text-xs">
            Risks
          </Text>
        </Flex>
      </Flex>

      <Flex vertical gap={0}>
        {conversations.map((conv) => {
          const tag = ASTRALIS_STATUS_TAG[conv.status];
          const isOverdue =
            conv.status === "awaiting" && conv.days_in_status > 3;

          return (
            <Flex
              key={`${conv.steward_name}-${conv.system_name}-${conv.status}`}
              justify="space-between"
              align="center"
              className="border-b border-solid border-b-[var(--ant-color-border)] py-3"
            >
              <Flex vertical gap={2}>
                <Text strong>{conv.steward_name}</Text>
                <Text type="secondary" className="text-xs">
                  {conv.system_name}
                </Text>
              </Flex>
              <Flex align="center" gap={8}>
                {isOverdue && (
                  <Text type="danger" className="text-xs">
                    {conv.days_in_status}d overdue
                  </Text>
                )}
                {tag && <Tag color={tag.color}>{tag.label}</Tag>}
              </Flex>
            </Flex>
          );
        })}
      </Flex>
    </Flex>
  );
};
