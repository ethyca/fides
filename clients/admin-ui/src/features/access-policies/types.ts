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

export enum ActionType {
  ALLOW = "allow",
  DENY = "deny",
}

export enum ConditionProperty {
  DATA_USE = "data_use",
  DATA_CATEGORIES = "data_category",
  DATA_SUBJECTS = "data_subject",
}

export enum ConditionOperator {
  ALL = "all",
  ANY = "any",
  NONE = "none",
}

export enum ConstraintType {
  CONSENT = "consent",
  USER = "user",
}

export enum ConsentValue {
  OPT_IN = "opt_in",
  OPT_OUT = "opt_out",
}

export enum UserOperator {
  EQUALS = "equals",
  NOT_EQUALS = "not_equals",
  GREATER_THAN = "greater_than",
  LESS_THAN = "less_than",
  CONTAINS = "contains",
}
