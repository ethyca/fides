import { BaseStepHookParams, Step } from "./types";

export const useCreateMonitorStep = (
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _params: BaseStepHookParams,
): Step => {
  return {
    title: "Create Monitor",
    description: "Create and run a data monitor",
    state: "wait", // TODO: Add monitor creation status when available
  };
};
