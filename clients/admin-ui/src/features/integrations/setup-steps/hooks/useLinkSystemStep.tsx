import { AntTypography } from "fidesui";
import Link from "next/link";

import { EDIT_SYSTEM_ROUTE, SYSTEM_ROUTE } from "~/features/common/nav/routes";
import { ConnectionConfigurationResponse } from "~/types/api/models/ConnectionConfigurationResponse";

import { BaseStepHookParams, Step } from "./types";

export interface LinkSystemStepParams extends BaseStepHookParams {
  connection?: ConnectionConfigurationResponse;
}

export const useLinkSystemStep = ({
  connection,
}: LinkSystemStepParams): Step => {
  // Check if the connection has a system_id property to determine if it's linked
  const isComplete = !!connection?.system_id;

  // Determine the appropriate link URL
  const linkUrl = isComplete
    ? EDIT_SYSTEM_ROUTE.replace("[id]", connection!.system_id!)
    : SYSTEM_ROUTE;

  return {
    title: (
      <Link href={linkUrl} passHref>
        <AntTypography.Link>Link System</AntTypography.Link>
      </Link>
    ),
    description: isComplete
      ? "System linked successfully"
      : "Link this integration to one of your systems. Use the 'Link integration' button in the Integrations tab.",
    state: isComplete ? "finish" : "process",
  };
};
