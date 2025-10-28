import {
  AntRadio as Radio,
  AntTypography as Typography,
  RadioChangeEvent,
} from "fidesui";
import { useCallback } from "react";

import type { ConsentMechanism } from "../types";

const ConsentMechanismRadioGroup = ({
  mechanism,
  onMechanismChange,
}: {
  mechanism: ConsentMechanism;
  onMechanismChange: (mechanism: ConsentMechanism) => void;
}) => {
  const handleMechanismChange = useCallback(
    (e: RadioChangeEvent) => {
      onMechanismChange(e.target.value);
    },
    [onMechanismChange],
  );

  return (
    <div className="mb-4">
      <Typography.Text className="text-sm font-medium">
        Consent Mechanism:
      </Typography.Text>
      <Radio.Group
        onChange={handleMechanismChange}
        value={mechanism}
        className="ml-2"
      >
        <Radio value="opt-out">Opt-out</Radio>
        <Radio value="opt-in">Opt-in</Radio>
      </Radio.Group>
      <Typography.Text type="secondary" className="ml-2 text-xs">
        (
        {mechanism === "opt-out"
          ? "All checked by default"
          : "All unchecked by default"}
        )
      </Typography.Text>
    </div>
  );
};

export default ConsentMechanismRadioGroup;
