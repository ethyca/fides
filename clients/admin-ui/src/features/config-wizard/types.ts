import { ValidTargets } from "~/types/api";

export enum SystemMethods {
  DATA_FLOW = "data-flow",
  MANUAL = "manual",
}

export type AddSystemMethods = ValidTargets | SystemMethods;
