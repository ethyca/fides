import type { SelectProps } from "fidesui";

import {
  ActionType,
  ConditionOperator,
  ConditionProperty,
  ConsentValue,
  ConstraintType,
  UserOperator,
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
  { value: ConditionOperator.NONE, label: "None" },
];

export const CONSTRAINT_TYPE_OPTIONS: RadioOption<ConstraintType>[] = [
  { value: ConstraintType.CONSENT, label: "Consent" },
  { value: ConstraintType.USER, label: "User" },
];

export const CONSENT_VALUE_OPTIONS: NonNullable<SelectProps["options"]> = [
  { value: ConsentValue.OPT_IN, label: "Opt in" },
  { value: ConsentValue.OPT_OUT, label: "Opt out" },
];

export const USER_OPERATOR_OPTIONS: NonNullable<SelectProps["options"]> = [
  { value: UserOperator.EQUALS, label: "Equals" },
  { value: UserOperator.NOT_EQUALS, label: "Not equals" },
  { value: UserOperator.GREATER_THAN, label: "Greater than" },
  { value: UserOperator.LESS_THAN, label: "Less than" },
  { value: UserOperator.CONTAINS, label: "Contains" },
];
