import { Switch } from "@fidesui/react";
import React, { ChangeEvent } from "react";

type ClassifyResultsToggleProps = {
  hideEmpty: boolean;
  onChange: (hideEmpty: boolean) => void;
};

const ClassifyResultsToggle = ({
  hideEmpty,
  onChange,
}: ClassifyResultsToggleProps) => {
  /*
    The <Switch> onChange function only takes functions with ChangeEvent<HTMLInputElement>
    as the input type. That's why the incoming function is being wrapped.
   */
  const handleToggle = (event: ChangeEvent<HTMLInputElement>) =>
    onChange(event.target.checked);

  return (
    <Switch
      colorScheme="secondary"
      isChecked={hideEmpty}
      onChange={handleToggle}
    />
  );
};

export default ClassifyResultsToggle;
