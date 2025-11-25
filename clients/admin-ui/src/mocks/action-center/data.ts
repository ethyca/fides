import { ConnectionType } from "~/types/api";

/**
 * Mock Okta monitor for action center testing
 */
export const mockOktaMonitor = {
  connection_type: ConnectionType.OKTA,
  secrets: null,
  saas_config: null,
  name: "Okta Identity Provider",
  key: "okta_identity_provider",
  last_monitored: "2025-11-21T15:30:00.000000Z",
  updates: {
    unlabeled: 0,
    in_review: 15,
    classifying: 0,
    removals: 0,
    approved: 5,
    classified_low_confidence: null,
    classified_high_confidence: null,
  },
  total_updates: 20,
  consent_status: null,
  connection_name: "Okta Production",
  has_failed_tasks: false,
};

/**
 * Mock Okta app asset for Identity Provider Monitor results
 * This matches StagedResourceAPIResponse structure
 */
export const mockOktaApp = {
  urn: "urn:okta:app:12345678-1234-1234-1234-123456789012",
  name: "Salesforce",
  description: "Customer relationship management platform",
  resource_type: "okta_app",
  diff_status: "addition",
  updated_at: "2024-01-15T10:30:00Z",
  monitor_config_id: "okta_identity_provider",
  system: "Okta Identity Provider",
  metadata: {
    app_type: "SAML_2_0",
    status: "ACTIVE",
    created: "2023-06-15T09:00:00Z",
    sign_on_url: "https://company.okta.com/app/salesforce/sso/saml",
    vendor_match_confidence: "medium",
    vendor_logo_url: "https://logo.clearbit.com/salesforce.com",
  },
  vendor_id: "fds.1234",
  system_id: "okta_system_001",
  system_key: null,
  data_uses: [],
  user_assigned_data_categories: null,
  user_assigned_data_uses: null,
  user_assigned_system_key: null,
};
