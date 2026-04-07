import { antTheme, CUSTOM_TAG_COLOR, Flex, Tag, Text } from "fidesui";

import { useGetAstralisQuery } from "~/features/dashboard/dashboard.slice";

import { useDashboardDrawer } from "./useDashboardDrawer";

const STATUS_TAG: Record<
  string,
  { color: CUSTOM_TAG_COLOR; label: string }
> = {
  in_progress: { color: CUSTOM_TAG_COLOR.INFO, label: "In Progress" },
  awaiting: { color: CUSTOM_TAG_COLOR.WARNING, label: "Awaiting Response" },
  completed: { color: CUSTOM_TAG_COLOR.SUCCESS, label: "Completed" },
};

export const AstralisDrawerContent = () => {
  const { token } = antTheme.useToken();
  const { data } = useGetAstralisQuery();
  const drawer = useDashboardDrawer();
  const metric = drawer?.type === "astralis" ? drawer.metric : undefined;

  const conversations = data?.conversations ?? [];

  return (
    <Flex vertical gap="middle">
      {metric && (
        <Text type="secondary" className="text-xs uppercase tracking-wide">
          Filtered by: {metric.replace(/_/g, " ")}
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
          const tag = STATUS_TAG[conv.status];
          const isOverdue =
            conv.status === "awaiting" && conv.days_in_status > 3;

          return (
            <Flex
              key={`${conv.steward_name}-${conv.system_name}`}
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
                <Tag color={tag.color}>{tag.label}</Tag>
              </Flex>
            </Flex>
          );
        })}
      </Flex>
    </Flex>
  );
};
