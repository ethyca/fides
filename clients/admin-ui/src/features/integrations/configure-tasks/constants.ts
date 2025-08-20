import { Operator } from "~/types/api";

// Mapping for operator display labels
export const operatorLabels: Record<Operator, string> = {
  [Operator.EQ]: "equals",
  [Operator.NEQ]: "not equals",
  [Operator.LT]: "less than",
  [Operator.LTE]: "less than or equal",
  [Operator.GT]: "greater than",
  [Operator.GTE]: "greater than or equal",
  [Operator.EXISTS]: "exists",
  [Operator.NOT_EXISTS]: "does not exist",
  [Operator.LIST_CONTAINS]: "list contains",
  [Operator.NOT_IN_LIST]: "not in list",
};
