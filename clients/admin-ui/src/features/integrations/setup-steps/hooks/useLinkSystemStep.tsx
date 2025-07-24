import { AntLink } from "fidesui";
import Link from "next/link";

import { EDIT_SYSTEM_ROUTE, SYSTEM_ROUTE } from "~/features/common/nav/routes";

import { BaseStepHookParams, Step } from "./types";

export const useLinkSystemStep = ({ connection }: BaseStepHookParams): Step => {
  // Check if the connection has a system_key property to determine if it's linked
  const isComplete = !!connection?.system_key;

  // Determine the appropriate link URL
  const linkUrl = isComplete
    ? EDIT_SYSTEM_ROUTE.replace("[id]", connection!.system_key!)
    : SYSTEM_ROUTE;

  return {
    title: "Link system",
    description: isComplete ? (
      <>
        <Link href={linkUrl} passHref>
          <AntLink>System linked</AntLink>
        </Link>{" "}
        successfully
      </>
    ) : (
      <>
        Link this integration in the{" "}
        <Link href={linkUrl} passHref>
          <AntLink>system inventory</AntLink>
        </Link>
        . Navigate to the appropriate system and within the integration tab
        select &quot;Link integration&quot;.
      </>
    ),
    state: isComplete ? "finish" : "process",
  };
};
