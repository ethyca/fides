import { BaseStepHookParams, Step } from "./types";

export const useLinkSystemStep = (
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _params: BaseStepHookParams,
): Step => {
  // For now, assume the system is not linked
  // This would typically be determined by some property in the API response
  // or connection data, but we'll use a placeholder for now
  const isComplete = false;

  return {
    title: "Link System",
    description: isComplete
      ? "System linked successfully"
      : "Link this integration to a system from the systems page",
    state: isComplete ? "finish" : "process",
  };
};
