import {
  ActionType,
  DrpAction,
  GroupOperator,
  Operator,
  PolicyResponse,
  RuleResponse,
} from "~/types/api";

/**
 * Mock policies for development and testing.
 * Includes the three seeded default policies plus a variety of custom policies
 * with realistic routing conditions.
 */
export const mockPolicies: PolicyResponse[] = [
  {
    name: "Default Consent Policy",
    key: "default_consent_policy",
    drp_action: null,
    execution_timeframe: 45,
    conditions: null,
    rules: [
      {
        name: "Default Consent Rule",
        key: "default_consent_rule",
        action_type: ActionType.CONSENT,
        storage_destination: null,
        masking_strategy: null,
      },
    ],
  },
  {
    name: "Default Erasure Policy",
    key: "default_erasure_policy",
    drp_action: DrpAction.DELETION,
    execution_timeframe: 45,
    conditions: null,
    rules: [
      {
        name: "Default Erasure Rule",
        key: "default_erasure_policy_rule",
        action_type: ActionType.ERASURE,
        storage_destination: null,
        masking_strategy: {
          strategy: "hmac",
        },
      },
    ],
  },
  {
    name: "Default Access Policy",
    key: "default_access_policy",
    drp_action: DrpAction.ACCESS,
    execution_timeframe: 45,
    conditions: null,
    rules: [
      {
        name: "Default Access Rule",
        key: "default_access_policy_rule",
        action_type: ActionType.ACCESS,
        storage_destination: null,
        masking_strategy: null,
      },
    ],
  },
  {
    name: "GDPR Erasure Policy",
    key: "gdpr_erasure_policy",
    drp_action: null,
    execution_timeframe: 30,
    conditions: {
      field_address: "privacy_request.location_regulations",
      operator: Operator.LIST_CONTAINS,
      value: "gdpr",
    },
    rules: [
      {
        name: "Erasure Rule",
        key: "erasure_rule",
        action_type: ActionType.ERASURE,
      } as RuleResponse,
    ],
  },
  {
    name: "CCPA Consumer Request",
    key: "ccpa_consumer_request",
    drp_action: null,
    execution_timeframe: 45,
    conditions: {
      field_address: "privacy_request.location_regulations",
      operator: Operator.LIST_CONTAINS,
      value: "ccpa",
    },
    rules: [
      {
        name: "Access Rule",
        key: "ccpa_access",
        action_type: ActionType.ACCESS,
      } as RuleResponse,
      {
        name: "Deletion Rule",
        key: "ccpa_delete",
        action_type: ActionType.ERASURE,
      } as RuleResponse,
    ],
  },
  {
    name: "Marketing Consent Policy",
    key: "marketing_consent_policy",
    drp_action: null,
    execution_timeframe: 7,
    conditions: null,
    rules: [
      {
        name: "Consent Rule",
        key: "consent_rule",
        action_type: ActionType.CONSENT,
      } as RuleResponse,
    ],
  },
  {
    name: "Data Portability Policy",
    key: "data_portability_policy",
    drp_action: null,
    execution_timeframe: 30,
    conditions: null,
    rules: [
      {
        name: "Export Rule",
        key: "export_rule",
        action_type: ActionType.ACCESS,
      } as RuleResponse,
    ],
  },
  {
    name: "LGPD Data Request Policy",
    key: "lgpd_data_request_policy",
    drp_action: null,
    execution_timeframe: 15,
    conditions: {
      field_address: "privacy_request.location_country",
      operator: Operator.EQ,
      value: "BR",
    },
    rules: [
      {
        name: "Access Rule",
        key: "lgpd_access",
        action_type: ActionType.ACCESS,
      } as RuleResponse,
    ],
  },
  {
    name: "Employee Data Deletion",
    key: "employee_data_deletion",
    drp_action: null,
    execution_timeframe: 60,
    conditions: null,
    rules: [
      {
        name: "HR Erasure",
        key: "hr_erasure",
        action_type: ActionType.ERASURE,
      } as RuleResponse,
    ],
  },
  {
    name: "Analytics Opt-Out Policy",
    key: "analytics_opt_out_policy",
    drp_action: null,
    execution_timeframe: 3,
    conditions: null,
    rules: [
      {
        name: "Analytics Consent",
        key: "analytics_consent",
        action_type: ActionType.CONSENT,
      } as RuleResponse,
    ],
  },
  {
    name: "Full Data Export Policy",
    key: "full_data_export_policy",
    drp_action: null,
    execution_timeframe: 30,
    conditions: null,
    rules: [
      {
        name: "Complete Export",
        key: "complete_export",
        action_type: ActionType.ACCESS,
      } as RuleResponse,
    ],
  },
  {
    name: "EU Data Access Request",
    key: "eu_data_access_request",
    drp_action: null,
    execution_timeframe: 30,
    conditions: {
      logical_operator: GroupOperator.OR,
      conditions: [
        {
          field_address: "privacy_request.location_country",
          operator: Operator.EQ,
          value: "FR",
        },
        {
          field_address: "privacy_request.location_country",
          operator: Operator.EQ,
          value: "DE",
        },
        {
          field_address: "privacy_request.location_country",
          operator: Operator.EQ,
          value: "IT",
        },
        {
          field_address: "privacy_request.location_country",
          operator: Operator.EQ,
          value: "ES",
        },
        {
          field_address: "privacy_request.location_country",
          operator: Operator.EQ,
          value: "NL",
        },
      ],
    },
    rules: [
      {
        name: "EU Access",
        key: "eu_access",
        action_type: ActionType.ACCESS,
      } as RuleResponse,
    ],
  },
  {
    name: "California Delete Request",
    key: "california_delete_request",
    drp_action: null,
    execution_timeframe: 45,
    conditions: {
      field_address: "privacy_request.location_groups",
      operator: Operator.LIST_CONTAINS,
      value: "ca",
    },
    rules: [
      {
        name: "CA Deletion",
        key: "ca_deletion",
        action_type: ActionType.ERASURE,
      } as RuleResponse,
    ],
  },
  {
    name: "Third Party Sharing Opt-Out",
    key: "third_party_sharing_opt_out",
    drp_action: null,
    execution_timeframe: 10,
    conditions: null,
    rules: [
      {
        name: "Sharing Consent",
        key: "sharing_consent",
        action_type: ActionType.CONSENT,
      } as RuleResponse,
    ],
  },
];
