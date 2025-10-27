import { Switch, Text } from "fidesui";
import { useCallback } from "react";

import type { ConsentMechanism } from "../types";

export const ConsentMechanismToggle = ({
  mechanism,
  onMechanismChange,
}: {
  mechanism: ConsentMechanism;
  onMechanismChange: (mechanism: ConsentMechanism) => void;
}) => {
  const handleToggle = useCallback(
    (checked: boolean) => {
      const newMechanism: ConsentMechanism = checked ? "opt-out" : "opt-in";
      onMechanismChange(newMechanism);
    },
    [onMechanismChange],
  );

  return (
    <div
      style={{
        marginBottom: "16px",
        display: "flex",
        alignItems: "center",
        gap: "12px",
      }}
    >
      <Text fontSize="sm" fontWeight="medium">
        Consent Mechanism:
      </Text>
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <Text
          fontSize="sm"
          color={mechanism === "opt-in" ? "primary.500" : "gray.500"}
        >
          Opt-in
        </Text>
        <Switch
          isChecked={mechanism === "opt-out"}
          onChange={(e) => handleToggle(e.target.checked)}
          size="sm"
        />
        <Text
          fontSize="sm"
          color={mechanism === "opt-out" ? "primary.500" : "gray.500"}
        >
          Opt-out
        </Text>
      </div>
      <Text fontSize="xs" color="gray.600">
        (
        {mechanism === "opt-out"
          ? "All checked by default"
          : "All unchecked by default"}
        )
      </Text>
    </div>
  );
};
