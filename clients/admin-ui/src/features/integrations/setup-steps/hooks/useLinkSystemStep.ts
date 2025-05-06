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

  return {
    title: "Link System",
    description: isComplete
      ? "System linked successfully"
      : "Link this integration to a system from the systems page",
    state: isComplete ? "finish" : "process",
  };
};
