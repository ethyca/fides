import { DataUseOption, SelectOption } from "./types";

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
