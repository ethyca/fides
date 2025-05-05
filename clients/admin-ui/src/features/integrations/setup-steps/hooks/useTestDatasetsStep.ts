import { BaseStepHookParams, Step } from "./types";

export const useTestDatasetsStep = (
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _params: BaseStepHookParams,
): Step => {
  return {
    title: "Test Datasets",
    description: "Validate the discovered datasets",
    state: "process", // TODO: Add dataset validation status when available
  };
};
