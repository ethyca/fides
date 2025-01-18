import { baseApi } from "~/features/common/api.slice";
import { Page_StagedResourceAPIResponse_ } from "~/types/api";
import { PaginationQueryParams } from "~/types/common/PaginationQueryParams";

import {
  MonitorSummaryPaginatedResponse,
  MonitorSystemAggregatePaginatedResponse,
} from "./types";

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
    addMonitorResultSystem: build.mutation<
      any,
      { monitor_config_key?: string; resolved_system_id?: string }
    >({
      query: (params) => ({
        method: "POST",
        url: `/plus/discovery-monitor/${params.monitor_config_key}/promote`,
        params: {
          resolved_system_id: params.resolved_system_id,
        },
      }),
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    ignoreMonitorResultSystem: build.mutation<
      any,
      { monitor_config_key?: string; resolved_system_id?: string }
    >({
      query: (params) => ({
        method: "POST",
        url: `/plus/discovery-monitor/${params.monitor_config_key}/mute`,
        params: {
          resolved_system_id: params.resolved_system_id,
        },
      }),
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    addMonitorResultAssets: build.mutation<any, { urnList?: string[] }>({
      query: (params) => ({
        method: "POST",
        url: `/plus/discovery-monitor/promote`,
        params: {
          staged_resource_urns: params.urnList,
        },
      }),
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    ignoreMonitorResultAssets: build.mutation<
      any,
      { urnList?: string[]; systemId?: string }
    >({
      query: (params) => ({
        method: "POST",
        url: `/plus/discovery-monitor/mute`,
        params: {
          staged_resource_urns: params.urnList,
        },
      }),
      invalidatesTags: ["Discovery Monitor Results"],
    }),
  }),
});

export const {
  useGetAggregateMonitorResultsQuery,
  useGetDiscoveredSystemAggregateQuery,
  useGetDiscoveredAssetsQuery,
  useAddMonitorResultSystemMutation,
  useIgnoreMonitorResultSystemMutation,
  useAddMonitorResultAssetsMutation,
  useIgnoreMonitorResultAssetsMutation,
} = actionCenterApi;
