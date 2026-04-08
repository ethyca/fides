import { Card, Flex, Statistic, Text } from "fidesui";

import {
  ASTRALIS_ACTIVE_KEY,
  ASTRALIS_AWAITING_KEY,
  ASTRALIS_METRICS,
} from "~/features/dashboard/constants";
import { useGetAstralisQuery } from "~/features/dashboard/dashboard.slice";

import styles from "./AstralisPanel.module.scss";

export const AstralisPanel = () => {
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
          const isActive = key === ASTRALIS_ACTIVE_KEY;
          const isOverdue = key === ASTRALIS_AWAITING_KEY && value > 0;

          return (
            <Flex key={key} align="center" gap="middle">
              <Statistic
                value={value}
                className={isOverdue ? styles.overdueValue : undefined}
              />
              {isActive && value > 0 && (
                <span className={styles.pulseDot} aria-hidden="true" />
              )}
              <Text
                type={isOverdue ? "warning" : "secondary"}
                className="text-xs"
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
