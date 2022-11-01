import { Switch } from "@fidesui/react";
import { setRevealPII } from "privacy-requests/privacy-requests.slice";
import React, { ChangeEvent } from "react";
import { useDispatch } from "react-redux";

const PIIToggle: React.FC = () => {
  const dispatch = useDispatch();
  const handleToggle = (event: ChangeEvent<HTMLInputElement>) =>
    dispatch(setRevealPII(event.target.checked));
  return <Switch colorScheme="secondary" onChange={handleToggle} />;
};

export default PIIToggle;
