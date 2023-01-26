import { Switch } from "@fidesui/react";
import { setRevealPII } from "privacy-requests/privacy-requests.slice";
import React, { ChangeEvent, useEffect } from "react";
import { useDispatch } from "react-redux";

const PIIToggle: React.FC = () => {
  const dispatch = useDispatch();
  const handleToggle = (event: ChangeEvent<HTMLInputElement>) =>
    dispatch(setRevealPII(event.target.checked));

  useEffect(() => {
    /*
      PII should default to hidden on page load.
      This ensures the state isn't reused as the user navigates around
   */
    dispatch(setRevealPII(false));
  }, [dispatch]);

  return <Switch colorScheme="secondary" onChange={handleToggle} />;
};

export default PIIToggle;
