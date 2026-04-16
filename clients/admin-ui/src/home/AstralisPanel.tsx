import { Card, Flex, Statistic, Text } from "fidesui";

import {
  ASTRALIS_ACTIVE_KEY,
  ASTRALIS_METRICS,
  ASTRALIS_RISKS_KEY,
} from "~/features/dashboard/constants";
import { useGetAstralisQuery } from "~/features/dashboard/dashboard.slice";

import styles from "./AstralisPanel.module.scss";

const ROW_COLORS: Record<string, string> = {
  success: "var(--ant-color-success)",
  warning: "var(--ant-color-warning)",
};

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
          const isActive = key === ASTRALIS_ACTIVE_KEY && value > 0;
          const isRisks = key === ASTRALIS_RISKS_KEY && value > 0;

          let variant: string | undefined;
          if (isActive) {
            variant = "success";
          } else if (isRisks) {
            variant = "warning";
          }

          const color = variant ? ROW_COLORS[variant] : undefined;

          return (
            <Flex
              key={key}
              align="baseline"
              gap="middle"
              className={isActive ? styles.pulse : undefined}
            >
              <Statistic
                value={value}
                styles={color ? { content: { color } } : undefined}
              />
              <Text
                type={variant ? undefined : "secondary"}
                className="text-sm"
                style={color ? { color } : undefined}
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
