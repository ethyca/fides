import { AccessPolicy } from "./access-policies.slice";

export interface SelectOption {
  label: string;
  value: string;
}

/**
 * AccessPolicy enriched with fields parsed from the embedded YAML.
 * Used by the list page to avoid parsing YAML in every component.
 */
export interface AccessPolicyListItem extends AccessPolicy {
  enabled: boolean;
  priority: number;
  decision?: "ALLOW" | "DENY";
}

export enum ActionType {
  ALLOW = "ALLOW",
  DENY = "DENY",
}

export enum ConditionProperty {
  DATA_USE = "data_use",
  DATA_CATEGORIES = "data_category",
  DATA_SUBJECTS = "data_subject",
}

export enum ConditionOperator {
  ALL = "all",
  ANY = "any",
}

/** PRD match dimension: { any: [...] } | { all: [...] } */
export interface MatchDimension {
  any?: string[];
  all?: string[];
}

export interface MatchBlock {
  data_category?: MatchDimension;
  data_use?: MatchDimension;
  data_subject?: MatchDimension;
  /** Custom taxonomy dimensions use their taxonomy_type as key */
  [key: string]: MatchDimension | undefined;
}

export enum ConstraintType {
  CONSENT = "consent",
  GEO_LOCATION = "geo_location",
  DATA_FLOW = "data_flow",
}

export enum ConsentRequirement {
  OPT_IN = "opt_in",
  OPT_OUT = "opt_out",
  NOT_OPT_IN = "not_opt_in",
  NOT_OPT_OUT = "not_opt_out",
}

export enum GeoOperator {
  IN = "in",
  NOT_IN = "not_in",
}

export enum DataFlowDirection {
  INGRESS = "ingress",
  EGRESS = "egress",
}

export enum DataFlowOperator {
  ANY_OF = "any_of",
  NONE_OF = "none_of",
}

export interface ConsentUnlessItem {
  type: "consent";
  privacy_notice_key: string;
  requirement: ConsentRequirement;
}

export interface GeoLocationUnlessItem {
  type: "geo_location";
  field: string;
  operator: GeoOperator;
  values: string[];
}

export interface DataFlowUnlessItem {
  type: "data_flow";
  direction: DataFlowDirection;
  operator: DataFlowOperator;
  systems: string[];
}

export type UnlessItem =
  | ConsentUnlessItem
  | GeoLocationUnlessItem
  | DataFlowUnlessItem;

export interface ActionBlock {
  message?: string;
}

export interface AccessPolicyYaml {
  fides_key?: string;
  name?: string;
  description?: string;
  enabled?: boolean;
  priority?: number;
  controls?: string[];
  decision: "ALLOW" | "DENY";
  match: MatchBlock;
  unless?: UnlessItem[];
  action?: ActionBlock;
}
