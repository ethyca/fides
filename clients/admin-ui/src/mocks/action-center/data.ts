import { ConnectionType, StagedResourceAPIResponse } from "~/types/api";
import { ApplicationStatus } from "~/types/api/models/ApplicationStatus";
import { AuthenticationProtocol } from "~/types/api/models/AuthenticationProtocol";
import { DiffStatus } from "~/types/api/models/DiffStatus";
import { StagedResourceTypeValue } from "~/types/api/models/StagedResourceTypeValue";
import { VendorMatchConfidence } from "~/types/api/models/VendorMatchConfidence";

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
    reviewed: 5,
    classified_low_confidence: null,
    classified_high_confidence: null,
  },
  total_updates: 20,
  consent_status: null,
  connection_name: "Okta Production",
  has_failed_tasks: false,
};

/**
 * Generate a mock Okta app asset for Identity Provider Monitor results
 * This matches StagedResourceAPIResponse structure
 */
const createMockOktaApp = (
  index: number,
  overrides?: Partial<StagedResourceAPIResponse>,
): StagedResourceAPIResponse => ({
  urn: `urn:okta:app:${String(index).padStart(8, "0")}-1234-1234-1234-123456789012`,
  name: overrides?.name || `App ${index}`,
  description: overrides?.description || `Description for app ${index}`,
  resource_type: StagedResourceTypeValue.OKTA_APP,
  diff_status: overrides?.diff_status || DiffStatus.ADDITION,
  updated_at: overrides?.updated_at || "2024-01-15T10:30:00Z",
  monitor_config_id: "okta_identity_provider",
  system: "Okta Identity Provider",
  metadata: {
    app_type: AuthenticationProtocol.SAML_2_0,
    status: ApplicationStatus.ACTIVE,
    created: "2023-06-15T09:00:00Z",
    sign_on_url: `https://company.okta.com/app/app${index}/sso/saml`,
    vendor_match_confidence: VendorMatchConfidence.MEDIUM,
    vendor_logo_url: `https://logo.clearbit.com/app${index}.com`,
  },
  vendor_id: overrides?.vendor_id || `fds.${index}`,
  system_id: "okta_system_001",
  system_key: null,
  data_uses: overrides?.data_uses || [],
  user_assigned_data_categories: null,
  user_assigned_data_uses: null,
  user_assigned_system_key: null,
});

/**
 * Mock Okta app asset for Identity Provider Monitor results
 */
export const mockOktaApp = createMockOktaApp(1, {
  name: "Salesforce",
  description: "Customer relationship management platform",
  vendor_id: "fds.1234",
});

/**
 * Generate multiple mock infrastructure systems for multi-page testing
 * Creates 75 items with varied properties for testing select all functionality
 */
export const generateMockInfrastructureSystems = () => {
  const apps = [];
  const vendors = ["fds.1234", "fds.5678", "fds.9012", "unknown"];
  const dataUses = [
    "advertising",
    "analytics",
    "customer_support",
    "fraud_detection",
    "marketing",
    "product_improvement",
    "security",
  ];
  const diffStatuses = [DiffStatus.ADDITION, DiffStatus.REMOVAL];
  const appNames = [
    "Salesforce",
    "Slack",
    "GitHub",
    "Jira",
    "Confluence",
    "Zoom",
    "Microsoft Teams",
    "Google Workspace",
    "AWS",
    "Azure",
    "Datadog",
    "Splunk",
    "New Relic",
    "PagerDuty",
    "ServiceNow",
  ];

  for (let i = 1; i <= 150; i += 1) {
    const vendorIndex = i % vendors.length;
    const statusIndex = i % diffStatuses.length;
    const nameIndex = i % appNames.length;
    const dataUsesCount = i % 4; // 0-3 data uses per app

    apps.push(
      createMockOktaApp(i, {
        name: `${appNames[nameIndex]}${i > appNames.length ? ` ${Math.floor(i / appNames.length)}` : ""}`,
        description: `${appNames[nameIndex]} integration for testing`,
        vendor_id: vendors[vendorIndex],
        diff_status: diffStatuses[statusIndex],
        data_uses: dataUsesCount > 0 ? dataUses.slice(0, dataUsesCount) : [],
        updated_at: new Date(
          2024,
          0,
          15 + (i % 30),
          10 + (i % 14),
          (i % 60) * 1000,
        ).toISOString(),
      }),
    );
  }

  return apps;
};

/**
 * Pre-generated mock infrastructure systems for use in handlers
 */
export const mockInfrastructureSystems = generateMockInfrastructureSystems();
