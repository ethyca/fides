import {
  ManualFieldRequestType,
  ManualTaskFieldType,
  Operator,
} from "~/types/api";

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
  [Operator.STARTS_WITH]: "starts with",
  [Operator.CONTAINS]: "contains",
  [Operator.LIST_INTERSECTS]: "list intersects",
  [Operator.LIST_SUBSET]: "list subset",
  [Operator.LIST_SUPERSET]: "list superset",
  [Operator.LIST_DISJOINT]: "list disjoint",
  [Operator.ENDS_WITH]: "ends with",
};

// Label mappings for field types and request types
export const FIELD_TYPE_LABELS: Record<ManualTaskFieldType, string> = {
  [ManualTaskFieldType.TEXT]: "Text",
  [ManualTaskFieldType.CHECKBOX]: "Checkbox",
  [ManualTaskFieldType.ATTACHMENT]: "Attachment",
};

export const REQUEST_TYPE_LABELS: Record<ManualFieldRequestType, string> = {
  [ManualFieldRequestType.ACCESS]: "Access",
  [ManualFieldRequestType.ERASURE]: "Erasure",
};
