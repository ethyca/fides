import { ButtonGroup } from "@fidesui/react";
import React from "react";

import { useAppSelector } from "~/app/hooks";

import { selectErrorRequests } from "../privacy-requests.slice";
import ReprocessButton from "./ReprocessButton";

const ActionButtons: React.FC = () => {
  const errorRequests = useAppSelector(selectErrorRequests);

  return errorRequests.length > 0 ? (
    <ButtonGroup flexDirection="row" size="sm" spacing="8px" variant="outline">
      <ReprocessButton />
    </ButtonGroup>
  ) : null;
};

export default ActionButtons;
