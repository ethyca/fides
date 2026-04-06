import { antTheme, Flex, Input, Text } from "fidesui";

import { useGetAstralisQuery } from "~/features/dashboard/dashboard.slice";

export const AgentStatusStrip = () => {
  const { token } = antTheme.useToken();
  const { data } = useGetAstralisQuery();

  const active = data?.active_conversations ?? 0;
  const awaiting = data?.awaiting_response ?? 0;

  return (
    <Flex
      align="center"
      justify="space-between"
      gap="middle"
      className="rounded-lg border border-solid border-[var(--ant-color-border)] px-6 py-3"
      style={{ backgroundColor: token.colorBgContainer }}
    >
      <Flex align="center" gap={8}>
        <span
          className="inline-block size-2 animate-pulse rounded-full"
          style={{ backgroundColor: token.colorSuccess }}
        />
        <Text type="secondary">
          Active: {active} PIA conversation{active !== 1 ? "s" : ""} · {awaiting}{" "}
          awaiting response
        </Text>
      </Flex>
      <Input
        placeholder="Ask me anything about your governance posture"
        disabled
        className="max-w-[400px]"
      />
    </Flex>
  );
};
