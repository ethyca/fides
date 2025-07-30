import { baseApi } from "~/features/common/api.slice";
import { getQueryParamsFromArray } from "~/features/common/utils";
import {
  ConsentStatus,
  DiffStatus,
  Page_ConsentBreakdown_,
  Page_StagedResourceAPIResponse_,
  Page_SystemStagedResourcesAggregateRecord_,
  PromoteResourcesResponse,
  StagedResourceAPIResponse,
} from "~/types/api";
import { PaginationQueryParams } from "~/types/common/PaginationQueryParams";

import { MonitorSummaryPaginatedResponse } from "./types";

interface MonitorResultSystemQueryParams {
  monitor_config_key: string;
  resolved_system_ids: string[];
}

interface DiscoveredAssetsQueryParams {
  key: string;
  system?: string;
  search?: string;
  diff_status?: DiffStatus[];
  sort_by?: string | string[];
  sort_asc?: boolean;
}

const actionCenterApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAggregateMonitorResults: build.query<
      MonitorSummaryPaginatedResponse,
      {
        search?: string;
      } & PaginationQueryParams
    >({
      query: ({ page = 1, size = 20, search }) => ({
        url: `/plus/discovery-monitor/aggregate-results`,
        params: { page, size, search, diff_status: "addition" },
      }),
      providesTags: ["Discovery Monitor Results"],
    }),
    getDiscoveredSystemAggregate: build.query<
      Page_SystemStagedResourcesAggregateRecord_,
      {
        key: string;
        search?: string;
        diff_status?: DiffStatus[];
      } & PaginationQueryParams
    >({
      query: ({ key, page = 1, size = 20, search, diff_status }) => ({
        url: `/plus/discovery-monitor/system-aggregate-results`,
        params: {
          monitor_config_id: key,
          page,
          size,
          search,
          diff_status,
        },
      }),
      providesTags: ["Discovery Monitor Results"],
    }),
    getDiscoveredAssets: build.query<
      Page_StagedResourceAPIResponse_,
      DiscoveredAssetsQueryParams & PaginationQueryParams
    >({
      query: ({
        key,
        system,
        page = 1,
        size = 20,
        search,
        diff_status = [DiffStatus.ADDITION],
        sort_by = ["consent_aggregated", "urn"],
        sort_asc = true,
      }) => ({
        url: `/plus/discovery-monitor/${key}/results?${getQueryParamsFromArray(
          Array.isArray(sort_by) ? sort_by : [sort_by],
          "sort_by",
        )}`,
        params: {
          resolved_system_id: system,
          page,
          size,
          search,
          diff_status,
          sort_asc,
        },
      }),
      providesTags: () => ["Discovery Monitor Results"],
    }),
    addMonitorResultSystems: build.mutation<
      PromoteResourcesResponse,
      MonitorResultSystemQueryParams
    >({
      query: ({ monitor_config_key, resolved_system_ids }) => {
        const params = getQueryParamsFromArray(
          resolved_system_ids,
          "resolved_system_ids",
        );
        return {
          method: "POST",
          url: `/plus/discovery-monitor/${monitor_config_key}/promote?${params}`,
        };
      },
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    ignoreMonitorResultSystems: build.mutation<
      string | null,
      MonitorResultSystemQueryParams
    >({
      query: ({ monitor_config_key, resolved_system_ids }) => {
        const params = getQueryParamsFromArray(
          resolved_system_ids,
          "resolved_system_ids",
        );
        return {
          method: "POST",
          url: `/plus/discovery-monitor/${monitor_config_key}/mute?${params}`,
        };
      },
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    addMonitorResultAssets: build.mutation<
      PromoteResourcesResponse,
      { urnList?: string[] }
    >({
      query: (params) => {
        const queryParams = new URLSearchParams();
        params.urnList?.forEach((urn) =>
          queryParams.append("staged_resource_urns", urn),
        );
        return {
          method: "POST",
          url: `/plus/discovery-monitor/promote?${queryParams}`,
        };
      },
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    ignoreMonitorResultAssets: build.mutation<any, { urnList?: string[] }>({
      query: (params) => {
        const queryParams = new URLSearchParams();
        params.urnList?.forEach((urn) =>
          queryParams.append("staged_resource_urns", urn),
        );
        return {
          method: "POST",
          url: `/plus/discovery-monitor/mute?${queryParams}`,
        };
      },
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    restoreMonitorResultAssets: build.mutation<any, { urnList?: string[] }>({
      query: (params) => {
        const queryParams = new URLSearchParams({
          status_to_set: DiffStatus.ADDITION,
        });
        params.urnList?.forEach((urn) =>
          queryParams.append("staged_resource_urns", urn),
        );
        return {
          method: "POST",
          url: `/plus/discovery-monitor/un-mute?${queryParams}`,
        };
      },
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    updateAssetsSystem: build.mutation<
      any,
      {
        monitorId: string;
        urnList: string[];
        systemKey: string;
      }
    >({
      query: (params) => ({
        method: "PATCH",
        url: `/plus/discovery-monitor/${params.monitorId}/results`,
        body: params.urnList.map((urn) => ({
          urn,
          user_assigned_system_key: params.systemKey,
        })),
      }),
      invalidatesTags: ["Discovery Monitor Results", "System Assets"],
    }),
    updateAssetsDataUse: build.mutation<
      any,
      { monitorId: string; urnList: string[]; dataUses: string[] }
    >({
      query: (params) => ({
        method: "PATCH",
        url: `/plus/discovery-monitor/${params.monitorId}/results`,
        body: params.urnList.map((urn) => ({
          urn,
          user_assigned_data_uses: params.dataUses,
        })),
      }),
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    // generic update assets mutation, necessary for non-destructive bulk data use updates
    updateAssets: build.mutation<
      any,
      {
        monitorId: string;
        assets: StagedResourceAPIResponse[];
      }
    >({
      query: (params) => ({
        method: "PATCH",
        url: `/plus/discovery-monitor/${params.monitorId}/results`,
        body: params.assets,
      }),
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    getConsentBreakdown: build.query<
      Page_ConsentBreakdown_,
      {
        stagedResourceUrn: string;
        status: ConsentStatus;
        page?: number;
        size?: number;
      } & PaginationQueryParams
    >({
      query: ({ stagedResourceUrn, status, page = 1, size = 20 }) => ({
        url: `/plus/discovery-monitor/staged_resource/${encodeURIComponent(
          stagedResourceUrn,
        )}/consent`,
        params: {
          status,
          page,
          size,
        },
      }),
    }),
    getWebsiteMonitorResourceFilters: build.query<
      Record<string, string[]>,
      {
        monitor_config_id: string;
        diff_status?: DiffStatus[];
        resource_type?: string[];
        data_uses?: string[];
        locations?: string[];
        consent_aggregated?: string[];
      }
    >({
      query: ({
        monitor_config_id,
        diff_status = [DiffStatus.ADDITION],
        resource_type,
        data_uses,
        locations,
        consent_aggregated,
      }) => {
        const params: Record<string, any> = {
          monitor_config_id,
          diff_status,
        };

        // Add filter parameters if they exist
        if (resource_type && resource_type.length > 0) {
          params.resource_type = resource_type;
        }
        if (data_uses && data_uses.length > 0) {
          params.data_uses = data_uses;
        }
        if (locations && locations.length > 0) {
          params.locations = locations;
        }
        if (consent_aggregated && consent_aggregated.length > 0) {
          params.consent_aggregated = consent_aggregated;
        }

        return {
          url: `/plus/filters/website_monitor_resources`,
          params,
        };
      },
      providesTags: ["Discovery Monitor Results"],
    }),
  }),
});

export const {
  useGetAggregateMonitorResultsQuery,
  useGetDiscoveredSystemAggregateQuery,
  useGetDiscoveredAssetsQuery,
  useAddMonitorResultSystemsMutation,
  useIgnoreMonitorResultSystemsMutation,
  useAddMonitorResultAssetsMutation,
  useIgnoreMonitorResultAssetsMutation,
  useRestoreMonitorResultAssetsMutation,
  useUpdateAssetsSystemMutation,
  useUpdateAssetsDataUseMutation,
  useUpdateAssetsMutation,
  useGetConsentBreakdownQuery,
  useGetWebsiteMonitorResourceFiltersQuery,
} = actionCenterApi;
