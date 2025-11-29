import { baseApi } from "~/features/common/api.slice";
import { buildArrayQueryParams } from "~/features/common/utils";
import { ConnectionType } from "~/types/api";
import type {
  Page_BasicSystemResponseExtended_,
  Page_Dataset_,
  Page_StagedResourceAPIResponse_,
  Page_Union_PrivacyRequestVerboseResponse__PrivacyRequestResponse__,
  PrivacyRequestStatus,
  DiffStatus,
} from "~/types/api";

/**
 * Dashboard API slice for summary data
 * Provides endpoints for fetching dashboard summary metrics
 */
const dashboardApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    /**
     * Get privacy request counts by status
     * Uses search endpoint with minimal page size to get just the total count
     */
    getPrivacyRequestCounts: build.query<
      { total: number },
      { status?: PrivacyRequestStatus[] }
    >({
      query: ({ status }) => ({
        url: `privacy-request/search`,
        method: "POST",
        body: {
          include_identities: false,
          include_custom_privacy_request_fields: false,
          ...(status && { status }),
        },
        params: {
          page: 1,
          size: 1, // We only need the total count
        },
      }),
      transformResponse: (
        response: Page_Union_PrivacyRequestVerboseResponse__PrivacyRequestResponse__,
      ) => ({
        total: response.total ?? 0,
      }),
      providesTags: () => ["Request"],
    }),

    /**
     * Get total system count
     * Uses minimal page size to get just the total count
     */
    getSystemCount: build.query<number, void>({
      query: () => ({
        url: `system`,
        params: {
          page: 1,
          size: 1, // We only need the total count
        },
      }),
      transformResponse: (response: Page_BasicSystemResponseExtended_) =>
        response.total ?? 0,
      providesTags: () => ["System"],
    }),

    /**
     * Get total dataset count
     * Uses minimal page size to get just the total count
     */
    getDatasetCount: build.query<number, void>({
      query: () => ({
        url: `dataset`,
        params: {
          page: 1,
          size: 1, // We only need the total count
        },
      }),
      transformResponse: (response: Page_Dataset_) => response.total ?? 0,
      providesTags: () => ["Datasets"],
    }),

    /**
     * Get total data-catalog dataset count (Fidesplus)
     * Uses minimal page size to get just the total count
     */
    getDataCatalogDatasetCount: build.query<number, void>({
      query: () => ({
        url: `/plus/data-catalog/dataset`,
        params: {
          page: 1,
          size: 1, // We only need the total count
        },
      }),
      transformResponse: (response: Page_StagedResourceAPIResponse_) =>
        response.total ?? 0,
      providesTags: () => ["Discovery Monitor Results"],
    }),

    /**
     * Get staged resource count by status for asset detection (website + infrastructure monitors)
     * Queries aggregate-results endpoint filtered by monitor type
     */
    getAssetDetectionCountByStatus: build.query<
      { total: number },
      { diff_status: DiffStatus[] }
    >({
      query: ({ diff_status }) => ({
        url: `/plus/discovery-monitor/aggregate-results`,
        params: {
          monitor_type: ["website", "infrastructure"],
          page: 1,
          size: 1, // We only need the total count
        },
      }),
      transformResponse: (response: {
        total: number;
      }) => ({
        total: response.total ?? 0,
      }),
      providesTags: () => ["Discovery Monitor Results"],
    }),

    /**
     * Get aggregate monitor results for website/infrastructure monitors
     * Returns total counts (aggregate-results only shows ADDITION for website, so we'll aggregate totals)
     * Queries all monitors and filters by connection_type on the frontend
     */
    getWebsiteInfrastructureAggregates: build.query<
      {
        total: number;
        uncategorized: number;
        in_review: number;
        categorized: number;
      },
      void
    >({
      query: () => {
        // Query all monitors (no monitor_type filter) - defaults to both website and datastore
        // We'll filter by connection_type on the frontend
        return {
          url: `/plus/discovery-monitor/aggregate-results`,
          params: {
            page: 1,
            size: 100, // API limit is 100
          },
        };
      },
      transformResponse: (response: {
        items: Array<{
          connection_type: ConnectionType;
          total_updates?: number;
        }>;
        total: number;
      }) => {
        // Filter for website and infrastructure (OKTA) monitors
        const websiteInfraTypes = [
          ConnectionType.WEBSITE,
          ConnectionType.TEST_WEBSITE,
          ConnectionType.OKTA,
        ];

        const websiteInfraItems = (response.items || []).filter((item) =>
          websiteInfraTypes.includes(item.connection_type),
        );

        // Aggregate-results for website/infrastructure only shows ADDITION status
        // So total_updates represents uncategorized assets
        let uncategorized = 0;
        let total = 0;

        for (const item of websiteInfraItems) {
          uncategorized += item.total_updates ?? 0;
          total += item.total_updates ?? 0;
        }

        // For now, we'll need to query staged resources directly for other statuses
        // This is a limitation - we'll set in_review and categorized to 0 for now
        // and will need backend support to get accurate counts
        return {
          total,
          uncategorized,
          in_review: 0, // TODO: Query staged resources with CLASSIFICATION_ADDITION, CLASSIFICATION_UPDATE
          categorized: 0, // TODO: Query staged resources with APPROVED
        };
      },
      providesTags: () => ["Discovery Monitor Results"],
    }),

    /**
     * Get aggregate monitor results for datastore monitors
     * Returns breakdown by status (unlabeled, in_review, classifying, approved, etc.)
     * Queries all monitors and filters by connection_type on the frontend
     */
    getDatastoreMonitorAggregates: build.query<
      {
        unlabeled: number;
        in_review: number;
        classifying: number;
        approved: number;
        total: number;
      },
      void
    >({
      query: () => {
        // Query all monitors (no monitor_type filter) - defaults to both website and datastore
        // We'll filter by connection_type on the frontend
        return {
          url: `/plus/discovery-monitor/aggregate-results`,
          params: {
            page: 1,
            size: 100, // API limit is 100
          },
        };
      },
      transformResponse: (response: {
        items: Array<{
          connection_type: ConnectionType;
          updates?: {
            unlabeled?: number;
            in_review?: number;
            classifying?: number;
            approved?: number;
          };
          total_updates?: number;
        }>;
      }) => {
        // Filter for datastore monitors (everything except website and OKTA)
        const websiteInfraTypes = [
          ConnectionType.WEBSITE,
          ConnectionType.TEST_WEBSITE,
          ConnectionType.OKTA,
        ];

        const datastoreItems = (response.items || []).filter(
          (item) => !websiteInfraTypes.includes(item.connection_type),
        );

        let unlabeled = 0;
        let in_review = 0;
        let classifying = 0;
        let approved = 0;
        let total = 0;

        for (const item of datastoreItems) {
          if (item.updates) {
            unlabeled += item.updates.unlabeled ?? 0;
            in_review += item.updates.in_review ?? 0;
            classifying += item.updates.classifying ?? 0;
            approved += item.updates.approved ?? 0;
          }
          total += item.total_updates ?? 0;
        }

        return {
          unlabeled,
          in_review,
          classifying,
          approved,
          total,
        };
      },
      providesTags: () => ["Discovery Monitor Results"],
    }),
  }),
});

export const {
  useGetPrivacyRequestCountsQuery,
  useGetSystemCountQuery,
  useGetDatasetCountQuery,
  useGetDataCatalogDatasetCountQuery,
  useGetAssetDetectionCountByStatusQuery,
  useGetWebsiteInfrastructureAggregatesQuery,
  useGetDatastoreMonitorAggregatesQuery,
} = dashboardApi;
