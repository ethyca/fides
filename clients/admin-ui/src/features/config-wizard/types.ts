import { ValidTargets } from "~/types/api";

export enum SystemMethods {
  RUNTIME = "runtime",
  MANUAL = "manual",
}

export type AddSystemMethods = ValidTargets | SystemMethods;
