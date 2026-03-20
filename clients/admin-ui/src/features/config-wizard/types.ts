import { ValidTargets } from "~/types/api";

export enum SystemMethods {
  MANUAL = "manual",
}

export type AddSystemMethods = ValidTargets | SystemMethods;
