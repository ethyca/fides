import type { SelectProps } from "fidesui";

import {
  ActionType,
  ConditionOperator,
  ConditionProperty,
  ConsentRequirement,
  ConstraintType,
  DataFlowDirection,
  DataFlowOperator,
  GeoOperator,
} from "./types";

interface RadioOption<T> {
  value: T;
  label: string;
}

export const ACTION_TYPE_OPTIONS: RadioOption<ActionType>[] = [
  { value: ActionType.ALLOW, label: "Allow" },
  { value: ActionType.DENY, label: "Deny" },
];

export const CONDITION_PROPERTY_OPTIONS: NonNullable<SelectProps["options"]> = [
  { value: ConditionProperty.DATA_USE, label: "Data use" },
  { value: ConditionProperty.DATA_CATEGORIES, label: "Data categories" },
  { value: ConditionProperty.DATA_SUBJECTS, label: "Data subjects" },
];

export const CONDITION_OPERATOR_OPTIONS: NonNullable<SelectProps["options"]> = [
  { value: ConditionOperator.ALL, label: "All" },
  { value: ConditionOperator.ANY, label: "Any" },
];

export const CONSTRAINT_TYPE_OPTIONS: RadioOption<ConstraintType>[] = [
  { value: ConstraintType.CONSENT, label: "Consent" },
  { value: ConstraintType.GEO_LOCATION, label: "Geo location" },
  { value: ConstraintType.DATA_FLOW, label: "Data flow" },
];

export const CONSENT_REQUIREMENT_OPTIONS: NonNullable<SelectProps["options"]> = [
  { value: ConsentRequirement.OPT_IN, label: "Opt in" },
  { value: ConsentRequirement.OPT_OUT, label: "Opt out" },
  { value: ConsentRequirement.NOT_OPT_IN, label: "Not opted in" },
  { value: ConsentRequirement.NOT_OPT_OUT, label: "Not opted out" },
];

export const GEO_OPERATOR_OPTIONS: NonNullable<SelectProps["options"]> = [
  { value: GeoOperator.IN, label: "In" },
  { value: GeoOperator.NOT_IN, label: "Not in" },
];

export const DATA_FLOW_DIRECTION_OPTIONS: NonNullable<SelectProps["options"]> = [
  { value: DataFlowDirection.INGRESS, label: "Ingress (source)" },
  { value: DataFlowDirection.EGRESS, label: "Egress (destination)" },
];

export const DATA_FLOW_OPERATOR_OPTIONS: NonNullable<SelectProps["options"]> = [
  { value: DataFlowOperator.ANY_OF, label: "Any of" },
  { value: DataFlowOperator.NONE_OF, label: "None of" },
];
