export interface SelectOption {
  label: string;
  value: string;
}

export interface DataUseOption {
  id: string;
  title: string;
  iconName: string;
}

export interface OnboardingFormState {
  industry: string | null;
  geography: string | null;
  selectedDataUses: string[];
  policyUrl: string;
}

export interface PolicyItem {
  id: string;
  title: string;
  description: string;
  isRecommendation: boolean;
  isNew?: boolean;
  isEnabled: boolean;
  violationCount: number;
  dataUseTags: string[];
  lastUpdated: string;
}

export interface PolicyCategory {
  id: string;
  title: string;
  drivenBy: string;
  policies: PolicyItem[];
}
