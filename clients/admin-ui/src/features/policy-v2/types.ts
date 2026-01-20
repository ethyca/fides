/**
 * Types for Policy Engine v2
 */

export type PolicyV2Action = "ALLOW" | "DENY";
export type PolicyV2MatchType = "key" | "taxonomy";
export type PolicyV2MatchOperator = "any" | "all";
export type PolicyV2ConstraintType = "privacy" | "context";
export type ConsentRequirement = "opt_in" | "not_opt_out";
export type EvaluateDecision = "ALLOW" | "DENY";

export interface TaxonomyMatchValue {
  taxonomy: string;
  element: string;
}

export interface PolicyV2RuleMatch {
  id?: string;
  match_type: PolicyV2MatchType;
  target_field: string;
  operator: PolicyV2MatchOperator;
  values: (string | TaxonomyMatchValue)[];
}

export interface PrivacyConstraintConfig {
  privacy_notice_key: string;
  requirement: ConsentRequirement;
}

export interface ContextConstraintConfig {
  field: string;
  operator: string;
  values: string[];
}

export interface PolicyV2RuleConstraint {
  id?: string;
  constraint_type: PolicyV2ConstraintType;
  configuration: PrivacyConstraintConfig | ContextConstraintConfig | Record<string, unknown>;
}

export interface PolicyV2Rule {
  id?: string;
  name: string;
  action: PolicyV2Action;
  order?: number;
  on_denial_message?: string | null;
  matches: PolicyV2RuleMatch[];
  constraints: PolicyV2RuleConstraint[];
}

export interface PolicyV2 {
  id: string;
  fides_key: string;
  name: string;
  description?: string | null;
  enabled: boolean;
  created_at?: string;
  updated_at?: string;
  rules: PolicyV2Rule[];
}

export interface PolicyV2Create {
  fides_key: string;
  name: string;
  description?: string | null;
  enabled?: boolean;
  rules: Omit<PolicyV2Rule, "id" | "order">[];
}

export interface PolicyV2Update {
  name?: string;
  description?: string | null;
  enabled?: boolean;
  rules?: Omit<PolicyV2Rule, "id" | "order">[];
}

export interface PolicyV2ListResponse {
  items: PolicyV2[];
  total: number;
}

// Evaluate types
export interface EvaluateSubjectContext {
  email?: string;
  phone_number?: string;
  fides_user_device_id?: string;
  external_id?: string;
}

export interface EvaluateEnvironmentContext {
  geo_location?: string;
}

export interface EvaluateContext {
  subject?: EvaluateSubjectContext;
  environment?: EvaluateEnvironmentContext;
  property_id?: string;
}

export interface EvaluateRequest {
  policy_key?: string;
  context?: EvaluateContext;
}

export interface ConstraintEvaluationResult {
  constraint_type: string;
  constraint_key: string;
  result: string;
  message?: string;
}

export interface EvaluatedRuleResult {
  rule_name: string;
  action: string;
  matched: boolean;
  result: string;
  constraints_evaluated?: ConstraintEvaluationResult[];
}

export interface EvaluatedPolicyResult {
  policy_key: string;
  policy_name: string;
  rules_evaluated: EvaluatedRuleResult[];
}

export interface PolicyViolation {
  policy_key: string;
  rule_name: string;
  action: string;
  message?: string;
  declaration_name?: string;
  data_use?: string;
}

export interface DeclarationEvaluationResult {
  declaration_name?: string;
  data_use: string;
  decision: EvaluateDecision;
  evaluated_policies: EvaluatedPolicyResult[];
  violations: PolicyViolation[];
}

export interface SystemEvaluationResult {
  system_fides_key: string;
  system_name: string;
  decision: EvaluateDecision;
  declarations_evaluated: DeclarationEvaluationResult[];
  violations: PolicyViolation[];
}

export interface EvaluateResponse {
  overall_decision: EvaluateDecision;
  policy_key?: string;
  total_systems_evaluated: number;
  total_violations: number;
  systems: SystemEvaluationResult[];
  warnings: string[];
}
