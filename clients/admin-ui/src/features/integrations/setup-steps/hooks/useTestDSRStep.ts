import { BaseStepHookParams, Step } from "./types";

export const useTestDSRStep = (
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _params: BaseStepHookParams,
): Step => {
  return {
    title: "Test DSR",
    description: "Run a test Data Subject Request",
    state: "wait", // TODO: Add DSR test status when available
  };
};
