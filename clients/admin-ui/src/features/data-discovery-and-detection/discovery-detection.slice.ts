import { createSelector, createSlice } from "@reduxjs/toolkit";
import queryString from "query-string";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import { DiffStatus, Page_StagedResource_ } from "~/types/api";

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
        method: "POST",
        url: `/plus/discovery-monitor/${params.monitor_config_id}/${params.staged_resource_urn}/confirm`,
        params: {},
      }),
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    muteResource: build.mutation<any, ResourceActionQueryParams>({
      query: ({ staged_resource_urn }) => ({
        method: "POST",
        url: `/plus/discovery-monitor/mute?${queryString.stringify(
          { staged_resource_urns: [staged_resource_urn] },
          { arrayFormat: "none" }
        )}`,
      }),
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    unmuteResource: build.mutation<any, ResourceActionQueryParams>({
      query: (params) => ({
        params,
        method: "POST",
        url: `/plus/discovery-monitor/un-mute?${queryString.stringify(
          { staged_resource_urns: [params.staged_resource_urn] },
          { arrayFormat: "none" }
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
          }
        )}`,
      }),
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    muteResources: build.mutation<any, BulkResourceActionQueryParams>({
      query: ({ staged_resource_urns }) => ({
        method: "POST",
        url: `/plus/discovery-monitor/mute?${queryString.stringify(
          { staged_resource_urns },
          { arrayFormat: "none" }
        )}`,
      }),
      invalidatesTags: ["Discovery Monitor Results"],
    }),
    promoteResources: build.mutation<any, BulkResourceActionQueryParams>({
      query: ({ staged_resource_urns }) => ({
        method: "POST",
        url: `/plus/discovery-monitor/promote?${queryString.stringify(
          { staged_resource_urns },
          { arrayFormat: "none" }
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
  (state) => state.page
);

export const selectPageSize = createSelector(
  selectDiscoveryDetectionState,
  (state) => state.pageSize
);
