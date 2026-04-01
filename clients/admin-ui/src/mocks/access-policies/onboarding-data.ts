import type { DataUseOption } from "~/features/access-policies/types";

export const mockDataUses: DataUseOption[] = [
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
  {
    id: "customer_support",
    title: "Customer Support",
    iconName: "Chat",
  },
  {
    id: "personalization",
    title: "Personalization",
    iconName: "UserProfile",
  },
];
