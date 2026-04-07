import { Flex, Text } from "fidesui";

import { HealthStatus } from "../types";

interface HealthBadgeProps {
  health: HealthStatus;
  count?: number;
}

function getBadgeConfig(health: HealthStatus, count?: number) {
  if (health === HealthStatus.HEALTHY) {
    return { dotColor: "#5a9a68", label: "Healthy" };
  }
  if (count !== undefined && count >= 3) {
    return { dotColor: "#d9534f", label: "Issues" };
  }
  return { dotColor: "#e59d47", label: "Issues" };
}

const HealthBadge = ({ health, count }: HealthBadgeProps) => {
  const config = getBadgeConfig(health, count);

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
