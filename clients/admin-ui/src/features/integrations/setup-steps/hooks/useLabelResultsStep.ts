import { BaseStepHookParams, Step } from "./types";

export const useLabelResultsStep = (
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _params: BaseStepHookParams,
): Step => {
  return {
    title: "Label Results",
    description: "Review and confirm the monitoring results",
    state: "wait", // TODO: Add labeling status when available
  };
};
