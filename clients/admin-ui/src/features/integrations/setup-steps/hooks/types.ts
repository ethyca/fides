import { ConnectionSystemTypeMap } from "~/types/api";

import type { ConnectionStatusData } from "../../ConnectionStatusNotice";

export type StepState = "finish" | "process" | "wait" | "error";

export interface Step {
  title: React.ReactNode;
  description: React.ReactNode;
  state: StepState;
}

export interface BaseStepHookParams {
  testData?: ConnectionStatusData;
  testIsLoading?: boolean;
  connectionOption?: ConnectionSystemTypeMap;
}
