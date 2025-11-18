import {
  Page_SystemStagedResourcesAggregateRecord_,
  SystemStagedResourcesAggregateRecord,
} from "~/types/api";
import { ApplicationStatus } from "~/types/api/models/ApplicationStatus";
import { AuthenticationProtocol } from "~/types/api/models/AuthenticationProtocol";
import { VendorMatchConfidence } from "~/types/api/models/VendorMatchConfidence";

/**
 * Mock data for Okta applications.
 * This should be replaced with actual API calls once the backend is ready.
 *
 * Note: The data structure includes fields needed for filtering (like diff_status)
 * which are part of StagedResourceAPIResponse but not SystemStagedResourcesAggregateRecord.
 * This is acceptable for stub/mock data.
 */
const MOCK_OKTA_APPS: (SystemStagedResourcesAggregateRecord & {
  diff_status?: string;
})[] = [
  {
    id: "urn:okta:app:12345678-1234-1234-1234-123456789012",
    name: "Salesforce",
    system_key: "okta_monitor_001",
    vendor_id: "fds.1234",
    total_updates: 1,
    diff_status: "addition",
    metadata: {
      app_type: AuthenticationProtocol.SAML_2_0,
      status: ApplicationStatus.ACTIVE,
      created: "2023-06-15T09:00:00Z",
      sign_on_url: "https://company.okta.com/app/salesforce/sso/saml",
      vendor_match_confidence: VendorMatchConfidence.HIGH,
      vendor_logo_url: "https://logo.clearbit.com/salesforce.com",
    },
  },
];

interface OktaStubClientParams {
  page?: number;
  size?: number;
  search?: string;
  diff_status?: string[];
  filterTab?: string;
}

export const oktaStubClient = {
  getDiscoveredSystemAggregate: (
    params: OktaStubClientParams,
  ): Page_SystemStagedResourcesAggregateRecord_ => {
    const { page = 1, size = 20, search } = params;

    // Apply search filter if provided
    let filteredItems = MOCK_OKTA_APPS;
    if (search) {
      const searchLower = search.toLowerCase();
      filteredItems = filteredItems.filter(
        (item) =>
          item.name?.toLowerCase().includes(searchLower) ??
          item.vendor_id?.toLowerCase().includes(searchLower),
      );
    }

    // Apply pagination
    const startIndex = (page - 1) * size;
    const endIndex = startIndex + size;
    const paginatedItems = filteredItems.slice(startIndex, endIndex);

    return {
      items: paginatedItems,
      total: filteredItems.length,
      page,
      size,
      pages: Math.ceil(filteredItems.length / size),
    };
  },

  getAllMockApps: (): SystemStagedResourcesAggregateRecord[] => {
    return MOCK_OKTA_APPS;
  },
};
