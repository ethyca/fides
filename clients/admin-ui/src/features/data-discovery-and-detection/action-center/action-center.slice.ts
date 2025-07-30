import { baseApi } from "~/features/common/api.slice";
import {
  buildArrayQueryParams,
  getQueryParamsFromArray,
} from "~/features/common/utils";
import {
  ConsentStatus,
  DiffStatus,
  Page_ConsentBreakdown_,
  Page_StagedResourceAPIResponse_,
  Page_SystemStagedResourcesAggregateRecord_,
  PromoteResourcesResponse,
  Schema,
  StagedResourceAPIResponse,
} from "~/types/api";
import {
  PaginationQueryParams,
  SearchQueryParams,
  SortQueryParams,
} from "~/types/query-params";

import { DiscoveredAssetsColumnKeys } from "./constants";
import { MonitorSummaryPaginatedResponse } from "./types";

interface MonitorResultSystemQueryParams {
  monitor_config_key: string;
  resolved_system_ids: string[];
}

interface DiscoveredAssetsFilterValues {
  resource_type?: string[];
  data_uses?: string[];
  locations?: string[];
  consent_aggregated?: string[];
}

const actionCenterApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAggregateMonitorResults: build.query<
      MonitorSummaryPaginatedResponse,
      SearchQueryParams & PaginationQueryParams
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
        diff_status?: DiffStatus[];
      } & SearchQueryParams &
        PaginationQueryParams
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
      SearchQueryParams &
        PaginationQueryParams &
        SortQueryParams<DiscoveredAssetsColumnKeys | "urn"> &
        DiscoveredAssetsFilterValues & {
          key: string;
          system?: string;
          diff_status?: DiffStatus[];
        }
    >({
      query: ({
        key,
        system,
        page = 1,
        size = 20,
        search,
        diff_status = [DiffStatus.ADDITION],
        sort_by = [DiscoveredAssetsColumnKeys.CONSENT_AGGREGATED, "urn"],
        sort_asc = true,
        resource_type,
        data_uses,
        locations,
        consent_aggregated,
      }) => {
        const params: SearchQueryParams &
          PaginationQueryParams &
          SortQueryParams<DiscoveredAssetsColumnKeys | "urn"> & {
            resolved_system_id?: string;
            diff_status?: DiffStatus[];
          } = {
          resolved_system_id: system,
          page,
          size,
          search,
          diff_status,
          sort_asc,
        };

        // Build URL query params for array parameters
        const sortByArray = Array.isArray(sort_by) ? sort_by : [sort_by];
        const urlParams = buildArrayQueryParams({
          sort_by: sortByArray,
          resource_type,
          data_uses,
          locations,
          consent_aggregated,
        });

        return {
          url: `/plus/discovery-monitor/${key}/results?${urlParams.toString()}`,
          params,
        };
      },
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
          url: `/plus/discovery-monitor/${monitor_config_key}/promote`,
          method: "POST",
          params: params ? new URLSearchParams(params) : new URLSearchParams(),
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
    ignoreMonitorResultAssets: build.mutation<string, { urnList?: string[] }>({
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
    restoreMonitorResultAssets: build.mutation<string, { urnList?: string[] }>({
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
      Schema,
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
      Schema,
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
      Schema,
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
        resolved_system_id: string;
        diff_status?: DiffStatus[];
      } & SearchQueryParams &
        DiscoveredAssetsFilterValues
    >({
      query: ({
        monitor_config_id,
        resolved_system_id,
        diff_status = [DiffStatus.ADDITION],
        search,
        resource_type,
        data_uses,
        locations,
        consent_aggregated,
      }) => {
        const params: SearchQueryParams & {
          monitor_config_id: string;
          diff_status?: DiffStatus[];
          resolved_system_id?: string;
        } = {
          monitor_config_id,
          resolved_system_id,
          diff_status,
        };

        // Add search parameter if it exists
        if (search) {
          params.search = search;
        }

        // Build URL query params for array parameters
        const urlParams = buildArrayQueryParams({
          resource_type,
          data_uses,
          locations,
          consent_aggregated,
        });

        const queryString = urlParams.toString();
        const url = queryString
          ? `/plus/filters/website_monitor_resources?${queryString}`
          : `/plus/filters/website_monitor_resources`;

        return {
          url,
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
