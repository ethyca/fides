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
