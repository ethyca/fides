import type { SelectProps } from "fidesui";

import {
  ActionType,
  ConditionOperator,
  ConditionProperty,
  ConsentRequirement,
  ConstraintType,
  DataFlowDirection,
  DataFlowOperator,
  DataUseOption,
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

export const GEOGRAPHY_OPTIONS: SelectOption[] = [
  { label: "EEA (European Economic Area)", value: "eea" },
  { label: "United States", value: "us" },
  { label: "United Kingdom", value: "uk" },
  { label: "Asia-Pacific (APAC)", value: "apac" },
  { label: "Global", value: "global" },
];

export const DATA_USES_BY_INDUSTRY: Record<string, DataUseOption[]> = {
  fintech: [
    { id: "fraud_detection", title: "Fraud Detection", iconName: "Security" },
    { id: "credit_scoring", title: "Credit Scoring", iconName: "ChartBar" },
    {
      id: "marketing_analytics",
      title: "Marketing Analytics",
      iconName: "Analytics",
    },
    {
      id: "regulatory_reporting",
      title: "Regulatory Reporting",
      iconName: "Building",
    },
  ],
  healthcare: [
    {
      id: "patient_care",
      title: "Patient Care Coordination",
      iconName: "Health",
    },
    { id: "clinical_research", title: "Clinical Research", iconName: "Search" },
    { id: "billing", title: "Billing & Claims", iconName: "Receipt" },
    {
      id: "population_health",
      title: "Population Health Analytics",
      iconName: "Analytics",
    },
  ],
  retail: [
    {
      id: "personalization",
      title: "Personalization",
      iconName: "UserProfile",
    },
    {
      id: "inventory_analytics",
      title: "Inventory Analytics",
      iconName: "ChartBar",
    },
    {
      id: "marketing_analytics",
      title: "Marketing Analytics",
      iconName: "Analytics",
    },
    {
      id: "fraud_prevention",
      title: "Fraud Prevention",
      iconName: "Security",
    },
  ],
  saas: [
    {
      id: "product_analytics",
      title: "Product Analytics",
      iconName: "Analytics",
    },
    {
      id: "user_segmentation",
      title: "User Segmentation",
      iconName: "GroupPresentation",
    },
    {
      id: "marketing_analytics",
      title: "Marketing Analytics",
      iconName: "ChartBar",
    },
    {
      id: "support_automation",
      title: "Support Automation",
      iconName: "Chat",
    },
  ],
  insurance: [
    { id: "underwriting", title: "Underwriting", iconName: "Document" },
    { id: "claims_processing", title: "Claims Processing", iconName: "Task" },
    { id: "risk_assessment", title: "Risk Assessment", iconName: "Warning" },
    {
      id: "regulatory_reporting",
      title: "Regulatory Reporting",
      iconName: "Building",
    },
  ],
  government: [
    {
      id: "citizen_services",
      title: "Citizen Services",
      iconName: "UserProfile",
    },
    {
      id: "public_safety",
      title: "Public Safety",
      iconName: "Security",
    },
    {
      id: "benefits_admin",
      title: "Benefits Administration",
      iconName: "Document",
    },
    {
      id: "records_management",
      title: "Records Management",
      iconName: "Folder",
    },
  ],
};

export const DEFAULT_DATA_USES: DataUseOption[] = [
  {
    id: "marketing_analytics",
    title: "Marketing Analytics",
    iconName: "Analytics",
  },
  { id: "fraud_detection", title: "Fraud Detection", iconName: "Security" },
  {
    id: "customer_support",
    title: "Customer Support",
    iconName: "Chat",
  },
  {
    id: "regulatory_reporting",
    title: "Regulatory Reporting",
    iconName: "Building",
  },
];

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
