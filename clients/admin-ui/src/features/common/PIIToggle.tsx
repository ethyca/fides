import { Switch } from "@fidesui/react";
import React, { ChangeEvent } from "react";

type PIIToggleProps = {
  revealPII: boolean;
  onChange: (revealPII: boolean) => void;
};

const PIIToggle = ({ revealPII, onChange }: PIIToggleProps) => {
  /*
    The <Switch> onChange function only takes functions with ChangeEvent<HTMLInputElement>
    as the input type. That's why the incoming function is being wrapped.
   */
  const handleToggle = (event: ChangeEvent<HTMLInputElement>) =>
    onChange(event.target.checked);

  return (
    <Switch
      colorScheme="secondary"
      isChecked={revealPII}
      onChange={handleToggle}
    />
  );
};

export default PIIToggle;
