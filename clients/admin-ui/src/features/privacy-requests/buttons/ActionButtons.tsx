import { ButtonGroup } from "fidesui";
import React from "react";

import { useAppSelector } from "~/app/hooks";

import { selectRetryRequests } from "../privacy-requests.slice";
import MoreButton from "./MoreButton";
import ReprocessButton from "./ReprocessButton";

const ActionButtons: React.FC = () => {
  const { errorRequests } = useAppSelector(selectRetryRequests);

  return (
    <ButtonGroup flexDirection="row" size="sm" spacing="8px" variant="outline">
      {errorRequests?.length > 0 && <ReprocessButton />}
      <MoreButton />
    </ButtonGroup>
  );
};

export default ActionButtons;
