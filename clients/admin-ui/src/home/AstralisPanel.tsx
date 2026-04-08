import { antTheme, Card, Flex, Statistic, Text } from "fidesui";

import { ASTRALIS_METRICS } from "~/features/dashboard/constants";
import { useGetAstralisQuery } from "~/features/dashboard/dashboard.slice";

export const AstralisPanel = () => {
  const { token } = antTheme.useToken();
  const { data, isLoading } = useGetAstralisQuery();

  return (
    <Card
      title="Astralis Agent Activity"
      variant="borderless"
      loading={isLoading}
      className="flex h-full flex-col [&_.ant-card-body]:flex-1 [&_.ant-card-body]:overflow-hidden"
    >
      <Flex wrap="wrap" gap={8}>
        {ASTRALIS_METRICS.map(({ key, label }) => {
          const value = data?.[key] ?? 0;
          const isActive = key === "active_conversations";
          const isOverdue = key === "awaiting_response" && value > 0;

          return (
            <Flex
              key={key}
              align="center"
              gap={6}
              className="min-w-[calc(50%-4px)] flex-1 rounded-md border border-solid border-[var(--ant-color-border)] px-3 py-2"
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
    </Card>
  );
};
