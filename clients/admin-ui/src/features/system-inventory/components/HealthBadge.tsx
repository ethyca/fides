import { Flex, Text } from "fidesui";

import { HEALTH_CONFIG } from "../constants";
import { HealthStatus } from "../types";

interface HealthBadgeProps {
  health: HealthStatus;
  count?: number;
}

const HealthBadge = ({ health, count }: HealthBadgeProps) => {
  const config = HEALTH_CONFIG[health];

  return (
    <Flex align="center" gap={6}>
      <div
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          backgroundColor: config.dotColor,
          flexShrink: 0,
        }}
      />
      <Text className="text-xs">
        {count !== undefined && count > 0 ? `${count} ` : ""}
        {count !== undefined && count > 1
          ? config.label.toLowerCase()
          : config.label}
      </Text>
    </Flex>
  );
};

export default HealthBadge;
