import { Switch } from "@fidesui/react";
import {
  selectRevealPII,
  setRevealPII,
} from "privacy-requests/privacy-requests.slice";
import React, { ChangeEvent } from "react";
import { useDispatch } from "react-redux";

import { useAppSelector } from "~/app/hooks";

const PIIToggle: React.FC = () => {
  const dispatch = useDispatch();
  const revealPII = useAppSelector(selectRevealPII);
  const handleToggle = (event: ChangeEvent<HTMLInputElement>) =>
    dispatch(setRevealPII(event.target.checked));

  return (
    <Switch
      colorScheme="secondary"
      onChange={handleToggle}
      isChecked={revealPII}
    />
  );
};

export default PIIToggle;
