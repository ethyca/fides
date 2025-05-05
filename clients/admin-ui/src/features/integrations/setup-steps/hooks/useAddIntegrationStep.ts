import { BaseStepHookParams, Step } from "./types";

export const useAddIntegrationStep = (
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _params: BaseStepHookParams,
): Step => {
  return {
    title: "Add Integration",
    description: "Configure and add your integration",
    state: "finish", // If we're viewing the integration, it's already added
  };
};
