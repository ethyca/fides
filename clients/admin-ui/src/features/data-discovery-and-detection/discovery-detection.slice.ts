import { createSelector, createSlice } from "@reduxjs/toolkit";
import queryString from "query-string";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import {
  DiffStatus,
  MonitorConfig,
  Page_MonitorConfig_,
  Page_StagedResourceAPIResponse_,
  Page_str_,
} from "~/types/api";

interface State {
  page?: number;
  pageSize?: number;
}

const initialState: State = {
  page: 1,
  pageSize: 50,
};

interface MonitorResultQueryParams {
  staged_resource_urn?: string;
  diff_status?: DiffStatus[];
  child_diff_status?: DiffStatus[];
  page?: number;
  size?: number;
  search?: string;
}

interface DatabaseByMonitorQueryParams {
  page: number;
  size: number;
  monitor_config_id: string;
  show_hidden?: boolean;
}

interface DatabaseByConnectionQueryParams {
  page: number;
  size: number;
  connection_config_key: string;
}

interface MonitorActionQueryParams {
  monitor_config_id: string;
}

interface ResourceActionQueryParams {
  staged_resource_urn?: string;
}
interface BulkResourceActionQueryParams {
  staged_resource_urns: string[];
}

interface ChangeResourceCategoryQueryParam {
  staged_resource_urn: string;
  user_assigned_data_categories: string[];
  monitor_config_id: string;
}

const discoveryDetectionApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getMonitorsByIntegration: build.query<Page_MonitorConfig_, any>({
      query: (params) => ({
        method: "GET",
        url: `/plus/discovery-monitor`,
        params,
      }),
      providesTags: ["Discovery Monitor Configs"],
    }),
    putDiscoveryMonitor: build.mutation<MonitorConfig, MonitorConfig>({
      query: (body) => ({
        method: "PUT",
        url: `/plus/discovery-monitor`,
        body: {
          ...body,
          // last_monitored is read-only and shouldn't be sent to the server
          last_monitored: undefined,
        },
      }),
      invalidatesTags: ["Discovery Monitor Configs"],
    }),
    getDatabasesByMonitor: build.query<Page_str_, DatabaseByMonitorQueryParams>(
      {
        query: (params) => ({
          method: "GET",
          url: `/plus/discovery-monitor/${params.monitor_config_id}/databases`,
        }),
      },
    ),
    getAvailableDatabasesByConnection: build.query<
      Page_str_,
      DatabaseByConnectionQueryParams
    >({
      query: (params) => ({
        method: "POST",
        url: `/plus/discovery-monitor/databases`,
        body: {
          name: "new-monitor",
          connection_config_key: params.connection_config_key,
          classify_params: {},
        },
      }),
    }),
    executeDiscoveryMonitor: build.mutation<any, MonitorActionQueryParams>({
      query: ({ monitor_config_id }) => ({
        method: "POST",
        url: `/plus/discovery-monitor/${monitor_config_id}/execute`,
      }),
      invalidatesTags: ["Discovery Monitor Configs"],
    }),
    deleteDiscoveryMonitor: build.mutation<any, MonitorActionQueryParams>({
      query: ({ monitor_config_id }) => ({
        method: "DELETE",
        url: `/plus/discovery-monitor/${monitor_config_id}`,
      }),
      invalidatesTags: ["Discovery Monitor Configs"],
    }),
    getMonitorResults: build.query<
      Page_StagedResourceAPIResponse_,
      MonitorResultQueryParams
    >({
      query: (params) => ({
        method: "GET",
        url: `/plus/discovery-monitor/results?${queryString.stringify(params, {
          arrayFormat: "none",
        })}`,
      }),
      providesTags: () => ["Discovery Monitor Results"],
    }),
    confirmResource: build.mutation<
      any,
      ResourceActionQueryParams & {
        monitor_config_id: string;
        unmute_children?: boolean;
        start_classification?: boolean;
        classify_monitored_resources?: boolean;
      }
    >({
      query: (params) => ({
        method: "POST",
        url: `/plus/discovery-monitor/${params.monitor_config_id}/${params.staged_resource_urn}/confirm?${queryString.stringify(
          {
            unmute_children: params.unmute_children,
            classify_monitored_resources: params.classify_monitored_resources,
          },
          { arrayFormat: "none" },
        )}`,
        params: {},
      }),
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    unmuteResource: build.mutation<any, ResourceActionQueryParams>({
      query: (params) => ({
        params,
        method: "POST",
        url: `/plus/discovery-monitor/un-mute?${queryString.stringify(
          { staged_resource_urns: [params.staged_resource_urn] },
          { arrayFormat: "none" },
        )}`,
      }),
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    muteResource: build.mutation<any, ResourceActionQueryParams>({
      query: ({ staged_resource_urn }) => ({
        method: "POST",
        url: `/plus/discovery-monitor/mute?${queryString.stringify(
          { staged_resource_urns: [staged_resource_urn] },
          { arrayFormat: "none" },
        )}`,
      }),
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    promoteResource: build.mutation<any, ResourceActionQueryParams>({
      query: (params) => ({
        method: "POST",
        url: `/plus/discovery-monitor/promote?${queryString.stringify(
          { staged_resource_urns: [params.staged_resource_urn] },
          {
            arrayFormat: "none",
          },
        )}`,
      }),
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    muteResources: build.mutation<any, BulkResourceActionQueryParams>({
      query: ({ staged_resource_urns }) => ({
        method: "POST",
        url: `/plus/discovery-monitor/mute?${queryString.stringify(
          { staged_resource_urns },
          { arrayFormat: "none" },
        )}`,
      }),
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    promoteResources: build.mutation<any, BulkResourceActionQueryParams>({
      query: ({ staged_resource_urns }) => ({
        method: "POST",
        url: `/plus/discovery-monitor/promote?${queryString.stringify(
          { staged_resource_urns },
          { arrayFormat: "none" },
        )}`,
      }),
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    updateResourceCategory: build.mutation<
      any,
      ChangeResourceCategoryQueryParam
    >({
      query: (params) => ({
        method: "PATCH",
        url: `/plus/discovery-monitor/${params.monitor_config_id}/results`,
        body: [
          {
            urn: params.staged_resource_urn,
            user_assigned_data_categories: params.user_assigned_data_categories,
          },
        ],
      }),

      invalidatesTags: ["Discovery Monitor Results"],
    }),
  }),
});

export const {
  useGetMonitorsByIntegrationQuery,
  usePutDiscoveryMonitorMutation,
  useGetDatabasesByMonitorQuery,
  useGetAvailableDatabasesByConnectionQuery,
  useLazyGetAvailableDatabasesByConnectionQuery,
  useExecuteDiscoveryMonitorMutation,
  useDeleteDiscoveryMonitorMutation,
  useGetMonitorResultsQuery,
  usePromoteResourceMutation,
  usePromoteResourcesMutation,
  useMuteResourceMutation,
  useMuteResourcesMutation,
  useConfirmResourceMutation,
  useUnmuteResourceMutation,
  useUpdateResourceCategoryMutation,
} = discoveryDetectionApi;

export const discoveryDetectionSlice = createSlice({
  name: "discoveryDetection",
  initialState,
  reducers: {},
});

export const { reducer } = discoveryDetectionSlice;

const selectDiscoveryDetectionState = (state: RootState) =>
  state.discoveryDetection;

export const selectPage = createSelector(
  selectDiscoveryDetectionState,
  (state) => state.page,
);

export const selectPageSize = createSelector(
  selectDiscoveryDetectionState,
  (state) => state.pageSize,
);
