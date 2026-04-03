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
  SelectOption,
} from "./types";

export const INDUSTRY_OPTIONS: SelectOption[] = [
  { label: "Fintech", value: "fintech" },
  { label: "Healthcare", value: "healthcare" },
  { label: "Retail & E-Commerce", value: "retail" },
  { label: "SaaS / Technology", value: "saas" },
  { label: "Insurance", value: "insurance" },
  { label: "Government", value: "government" },
];

/** Icon for each data use card. Fideslang has no icon metadata. */
export const DATA_USE_ICON: Record<string, string> = {
  "essential.fraud_detection": "Security",
  "analytics.reporting": "ChartBar",
  "essential.service.payment_processing": "Receipt",
  "essential.legal_obligation": "Building",
  "marketing.advertising.profiling": "GroupPresentation",
  "personalize.content": "UserProfile",
  "essential.service.operations.support": "Chat",
  "essential.service.operations": "Task",
  third_party_sharing: "Folder",
  "essential.service.security": "Security",
  employment: "Document",
  "marketing.communications.email": "Chat",
  "functional.service.improve": "Analytics",
  train_ai_system: "Analytics",
  "functional.storage.privacy_preferences": "Security",
  "marketing.advertising.third_party.targeted": "ChartBar",
};

interface RadioOption<T> {
  value: T;
  label: string;
}

export const ACTION_TYPE_OPTIONS: RadioOption<ActionType>[] = [
  { value: ActionType.ALLOW, label: "Allow" },
  { value: ActionType.DENY, label: "Deny" },
];

export const DECISION_LABELS: Record<ActionType, string> = {
  [ActionType.ALLOW]: "Allow",
  [ActionType.DENY]: "Deny",
};

export const CONDITION_PROPERTY_OPTIONS: NonNullable<SelectProps["options"]> = [
  { value: ConditionProperty.DATA_USE, label: "Data use" },
  { value: ConditionProperty.DATA_CATEGORIES, label: "Data categories" },
  { value: ConditionProperty.DATA_SUBJECTS, label: "Data subjects" },
];

export const CONDITION_OPERATOR_OPTIONS: NonNullable<SelectProps["options"]> = [
  { value: ConditionOperator.ALL, label: "All of" },
  { value: ConditionOperator.ANY, label: "Any of" },
];

export const CONSTRAINT_TYPE_OPTIONS: RadioOption<ConstraintType>[] = [
  { value: ConstraintType.CONSENT, label: "Consent" },
  { value: ConstraintType.GEO_LOCATION, label: "Geo location" },
  { value: ConstraintType.DATA_FLOW, label: "Data flow" },
];

export const CONSENT_REQUIREMENT_OPTIONS: NonNullable<SelectProps["options"]> =
  [
    { value: ConsentRequirement.OPT_IN, label: "Opt in" },
    { value: ConsentRequirement.OPT_OUT, label: "Opt out" },
    { value: ConsentRequirement.NOT_OPT_IN, label: "Not opted in" },
    { value: ConsentRequirement.NOT_OPT_OUT, label: "Not opted out" },
  ];

export const GEO_OPERATOR_OPTIONS: NonNullable<SelectProps["options"]> = [
  { value: GeoOperator.IN, label: "In" },
  { value: GeoOperator.NOT_IN, label: "Not in" },
];

export const DATA_FLOW_DIRECTION_OPTIONS: NonNullable<SelectProps["options"]> =
  [
    { value: DataFlowDirection.INGRESS, label: "Ingress (source)" },
    { value: DataFlowDirection.EGRESS, label: "Egress (destination)" },
  ];

export const DATA_FLOW_OPERATOR_OPTIONS: NonNullable<SelectProps["options"]> = [
  { value: DataFlowOperator.ANY_OF, label: "Any of" },
  { value: DataFlowOperator.NONE_OF, label: "None of" },
];
