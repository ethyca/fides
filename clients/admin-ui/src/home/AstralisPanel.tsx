import { antTheme, Card, Flex, Statistic } from "fidesui";

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
      className="h-full"
    >
      <Flex vertical gap="large">
        {ASTRALIS_METRICS.map(({ key, label }) => {
          const value = data?.[key] ?? 0;
          const isActive = key === "active_conversations";
          const isOverdue = key === "awaiting_response" && value > 0;

          return (
            <Flex key={key} align="center" gap={8}>
              {isActive && (
                <span
                  className="inline-block size-2 animate-pulse rounded-full"
                  style={{ backgroundColor: token.colorSuccess }}
                />
              )}
              <Statistic
                value={value}
                suffix={label}
                valueStyle={{
                  color: isOverdue ? token.colorWarning : undefined,
                }}
              />
            </Flex>
          );
        })}
      </Flex>
    </Card>
  );
};
