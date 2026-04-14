import { Flex, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";

import { HealthStatus } from "../types";

interface HealthBadgeProps {
  health: HealthStatus;
  count?: number;
}

function getBadgeConfig(health: HealthStatus, count?: number) {
  if (health === HealthStatus.HEALTHY) {
    return { dotColor: palette.FIDESUI_SUCCESS, label: "Healthy" };
  }
  if (count !== undefined && count >= 3) {
    return { dotColor: palette.FIDESUI_ERROR, label: "Risks" };
  }
  return { dotColor: palette.FIDESUI_WARNING, label: "Risks" };
}

const HealthBadge = ({ health, count }: HealthBadgeProps) => {
  const config = getBadgeConfig(health, count);
  const displayLabel =
    count !== undefined && count === 1 ? "Risk" : config.label;

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
        {displayLabel.toLowerCase()}
      </Text>
    </Flex>
  );
};

export default HealthBadge;
