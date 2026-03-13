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

// YAML format interfaces

export interface ConditionClause {
  operator?: ConditionOperator;
  values: string[];
}

export interface ConditionMap {
  data_category?: ConditionClause;
  data_use?: ConditionClause;
  data_subject?: ConditionClause;
}

export interface ConsentConstraintItem {
  consent: {
    preference_key: string[];
    value: ConsentValue;
  };
}

export interface UserConstraintItem {
  user: {
    key: string;
    value: string | number;
    operator: UserOperator;
  };
}

export type ConstraintItem = ConsentConstraintItem | UserConstraintItem;

export interface UnlessBlock {
  any?: ConstraintItem[];
  all?: ConstraintItem[];
}

export interface AccessPolicyYaml {
  fides_key?: string;
  name: string;
  description?: string;
  enabled?: boolean;
  allow?: ConditionMap;
  deny?: ConditionMap;
  unless?: UnlessBlock;
}
