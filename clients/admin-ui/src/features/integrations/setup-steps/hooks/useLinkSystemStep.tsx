import { AntLink } from "fidesui";
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
  // Check if the connection has a system_key property to determine if it's linked
  const isComplete = !!connection?.system_key;

  // Determine the appropriate link URL
  const linkUrl = isComplete
    ? EDIT_SYSTEM_ROUTE.replace("[id]", connection!.system_key!)
    : SYSTEM_ROUTE;

  return {
    title: "Link System",
    description: isComplete ? (
      <>
        <Link href={linkUrl} passHref>
          <AntLink>System linked</AntLink>
        </Link>{" "}
        successfully
      </>
    ) : (
      <>
        Link this integration to{" "}
        <Link href={linkUrl} passHref>
          <AntLink>one of your systems</AntLink>
        </Link>
        . Use the &apos;Link integration&apos; button in the Integrations tab.
      </>
    ),
    state: isComplete ? "finish" : "process",
  };
};
