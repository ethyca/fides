import { baseApi } from "~/features/common/api.slice";
import { getQueryParamsFromArray } from "~/features/common/utils";
import { Page_StagedResourceAPIResponse_ } from "~/types/api";
import { PaginationQueryParams } from "~/types/common/PaginationQueryParams";

import {
  MonitorSummaryPaginatedResponse,
  MonitorSystemAggregatePaginatedResponse,
} from "./types";

interface MonitorResultSystemQueryParams {
  monitor_config_key: string;
  resolved_system_ids: string[];
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
      MonitorSystemAggregatePaginatedResponse,
      {
        key: string;
        search?: string;
      } & PaginationQueryParams
    >({
      query: ({ key, page = 1, size = 20, search }) => ({
        url: `/plus/discovery-monitor/system-aggregate-results`,
        params: {
          monitor_config_id: key,
          page,
          size,
          search,
          diff_status: "addition",
        },
      }),
      providesTags: ["Discovery Monitor Results"],
    }),
    getDiscoveredAssets: build.query<
      Page_StagedResourceAPIResponse_,
      { key: string; system: string; search: string } & PaginationQueryParams
    >({
      query: ({ key, system, page = 1, size = 20, search }) => ({
        url: `/plus/discovery-monitor/${key}/results`,
        params: {
          resolved_system_id: system,
          page,
          size,
          search,
          diff_status: "addition",
        },
      }),
      providesTags: () => ["Discovery Monitor Results"],
    }),
    addMonitorResultSystems: build.mutation<
      any,
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
      any,
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
    addMonitorResultAssets: build.mutation<any, { urnList?: string[] }>({
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
          system_key: params.systemKey,
        })),
      }),
      invalidatesTags: ["Discovery Monitor Results"],
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
  useUpdateAssetsSystemMutation,
} = actionCenterApi;
