import { ConsentStatus } from "~/types/api";

import { DiscoveryErrorStatuses } from "../constants";

/**
 * Determines if the given consent status represents a compliance issue.
 * Returns true for error statuses (without consent, pre-consent, CMP error).
 */
const hasConsentComplianceIssue = (
  consentStatus: ConsentStatus | null | undefined,
): boolean => {
  if (!consentStatus) {
    return false;
  }
  return DiscoveryErrorStatuses.includes(consentStatus);
};

export default hasConsentComplianceIssue;
