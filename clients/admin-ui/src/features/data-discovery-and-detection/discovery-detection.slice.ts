import { createSelector, createSlice } from "@reduxjs/toolkit";
import queryString from "query-string";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import {
  DiffStatus,
  DiscoveryMonitorConfig,
  Page_DiscoveryMonitorConfig_,
  Page_StagedResource_,
} from "~/types/api";

interface State {
  page?: number;
  pageSize?: number;
}

const initialState: State = {
  page: 1,
  pageSize: 50,
};

interface MonitorQueryParams {
  page?: number;
  size?: number;
}

interface MonitorResultQueryParams {
  staged_resource_urn?: string;
  diff_status?: DiffStatus[];
  child_diff_status?: DiffStatus[];
  page?: number;
  size?: number;
}

interface ResourceActionQueryParams {
  staged_resource_urn?: string;
}

interface ChangeResourceCategoryQueryParam {
  staged_resource_urn: string;
  user_assigned_data_categories: string[];
  monitor_config_id: string;
}

const discoveryDetectionApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllMonitors: build.query<
      Page_DiscoveryMonitorConfig_,
      MonitorQueryParams
    >({
      query: (params) => ({
        params,
        method: "GET",
        url: `/plus/discovery-monitor`,
      }),
      providesTags: () => ["Discovery Monitor Configs"],
    }),
    getMonitorResults: build.query<
      Page_StagedResource_,
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
      ResourceActionQueryParams & { monitor_config_id: string }
    >({
      query: (params) => ({
        params,
        method: "POST",
        url: `/plus/discovery-monitor/${params.monitor_config_id}/${params.staged_resource_urn}/confirm`,
      }),
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    muteResource: build.mutation<any, ResourceActionQueryParams>({
      query: (params) => ({
        params,
        method: "POST",
        url: `/plus/discovery-monitor/${params.staged_resource_urn}/mute`,
      }),
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    unmuteResource: build.mutation<any, ResourceActionQueryParams>({
      query: (params) => ({
        params,
        method: "POST",
        url: `/plus/discovery-monitor/${params.staged_resource_urn}/un-mute`,
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
          }
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
  useGetAllMonitorsQuery,
  useGetMonitorResultsQuery,
  usePromoteResourceMutation,
  useMuteResourceMutation,
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
  (state) => state.page
);

export const selectPageSize = createSelector(
  selectDiscoveryDetectionState,
  (state) => state.pageSize
);

const EMPTY_MONITORS: DiscoveryMonitorConfig[] = [];

export const selectAllMonitors = createSelector(
  [(RootState) => RootState, selectPage, selectPageSize],
  (RootState, page, pageSize) => {
    const data = discoveryDetectionApi.endpoints.getAllMonitors.select({
      page,
      size: pageSize,
    })(RootState)?.data;
    return data ? data.items : EMPTY_MONITORS;
  }
);
