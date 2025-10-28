import { AntTypography as Typography, Switch } from "fidesui";
import { useCallback } from "react";

import type { ConsentMechanism } from "../types";

const ConsentMechanismToggle = ({
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
    <div className="mb-4 flex items-center gap-3">
      <Typography.Text className="text-sm font-medium">
        Consent Mechanism:
      </Typography.Text>
      <div className="flex items-center gap-2">
        <Typography.Text
          className="text-sm"
          type={mechanism === "opt-in" ? undefined : "secondary"}
        >
          Opt-in
        </Typography.Text>
        <Switch
          isChecked={mechanism === "opt-out"}
          onChange={(e) => handleToggle(e.target.checked)}
          size="sm"
        />
        <Typography.Text
          className="text-sm"
          type={mechanism === "opt-out" ? undefined : "secondary"}
        >
          Opt-out
        </Typography.Text>
      </div>
      <Typography.Text type="secondary" className="text-xs">
        (
        {mechanism === "opt-out"
          ? "All checked by default"
          : "All unchecked by default"}
        )
      </Typography.Text>
    </div>
  );
};

export default ConsentMechanismToggle;
