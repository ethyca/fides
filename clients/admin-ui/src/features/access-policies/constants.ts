import type { SelectProps } from "fidesui";

import {
  ActionType,
  ConditionOperator,
  ConditionProperty,
  ConsentRequirement,
  ConstraintType,
  DataFlowDirection,
  DataFlowOperator,
  DataUseDisplayInfo,
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

export const DATA_USE_DISPLAY: Record<string, DataUseDisplayInfo> = {
  fraud_detection: { title: "Fraud Detection", iconName: "Security" },
  credit_scoring: { title: "Credit Scoring", iconName: "ChartBar" },
  marketing_analytics: { title: "Marketing Analytics", iconName: "Analytics" },
  regulatory_reporting: {
    title: "Regulatory Reporting",
    iconName: "Building",
  },
  patient_care: { title: "Patient Care Coordination", iconName: "Health" },
  clinical_research: { title: "Clinical Research", iconName: "Search" },
  billing: { title: "Billing & Claims", iconName: "Receipt" },
  population_health: {
    title: "Population Health Analytics",
    iconName: "Analytics",
  },
  personalization: { title: "Personalization", iconName: "UserProfile" },
  inventory_analytics: {
    title: "Inventory Analytics",
    iconName: "ChartBar",
  },
  fraud_prevention: { title: "Fraud Prevention", iconName: "Security" },
  product_analytics: { title: "Product Analytics", iconName: "Analytics" },
  user_segmentation: {
    title: "User Segmentation",
    iconName: "GroupPresentation",
  },
  support_automation: { title: "Support Automation", iconName: "Chat" },
  underwriting: { title: "Underwriting", iconName: "Document" },
  claims_processing: { title: "Claims Processing", iconName: "Task" },
  risk_assessment: { title: "Risk Assessment", iconName: "Warning" },
  citizen_services: { title: "Citizen Services", iconName: "UserProfile" },
  public_safety: { title: "Public Safety", iconName: "Security" },
  benefits_admin: {
    title: "Benefits Administration",
    iconName: "Document",
  },
  records_management: { title: "Records Management", iconName: "Folder" },
  customer_support: { title: "Customer Support", iconName: "Chat" },
};

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
