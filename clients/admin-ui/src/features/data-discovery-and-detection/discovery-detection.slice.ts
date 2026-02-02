import { createSelector, createSlice } from "@reduxjs/toolkit";
import queryString from "query-string";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import {
  DiffStatus,
  EditableMonitorConfig,
  MonitorConfig,
  Page_MonitorStatusResponse_,
  Page_StagedResourceAPIResponse_,
  Page_str_,
  Schema,
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
  monitor_config_id: string;
  staged_resource_urn: string;
  user_assigned_data_categories?: string[];
  user_assigned_system_key?: string;
}

// Identity Provider Monitor interfaces (Okta-specific)
interface IdentityProviderMonitorResultsQueryParams {
  monitor_config_key: string;
  page?: number;
  size?: number;
  search?: string;
  diff_status?: DiffStatus | DiffStatus[];
  status?: string | string[];
  vendor_id?: string | string[];
  data_uses?: string[];
}

interface IdentityProviderMonitorExecuteParams {
  monitor_config_key: string;
}

interface IdentityProviderResourceActionParam {
  monitor_config_key: string;
  urn: string;
}

interface IdentityProviderResourceBulkActionParam {
  monitor_config_key: string;
  urns?: string[];
  bulkSelection?: {
    filters?: {
      search?: string;
      diff_status?: DiffStatus | DiffStatus[];
      vendor_id?: string | string[];
      data_uses?: string[];
    };
    exclude_urns?: string[];
  };
}

interface IdentityProviderMonitorFiltersQueryParams {
  monitor_config_key: string;
  diff_status?: DiffStatus | DiffStatus[];
  vendor_id?: string | string[];
  data_uses?: string[];
}

export interface IDPMonitorFiltersResponse {
  diff_status: string[];
  vendor_id: string[];
  data_uses: string[];
}

const discoveryDetectionApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getMonitorsByIntegration: build.query<Page_MonitorStatusResponse_, any>({
      query: (params) => ({
        method: "GET",
        url: `/plus/discovery-monitor`,
        params,
      }),
      providesTags: ["Discovery Monitor Configs"],
    }),
    putDiscoveryMonitor: build.mutation<MonitorConfig, EditableMonitorConfig>({
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
        diff_statuses_to_classify?: DiffStatus[];
      }
    >({
      query: (params) => ({
        method: "POST",
        url: `/plus/discovery-monitor/${params.monitor_config_id}/${params.staged_resource_urn}/confirm?${queryString.stringify(
          {
            unmute_children: params.unmute_children,
            classify_monitored_resources: params.classify_monitored_resources,
            diff_statuses_to_classify: params.diff_statuses_to_classify,
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
    unmuteResources: build.mutation<any, BulkResourceActionQueryParams>({
      query: (params) => ({
        params,
        method: "POST",
        url: `/plus/discovery-monitor/un-mute?${queryString.stringify(
          { staged_resource_urns: params.staged_resource_urns },
          { arrayFormat: "none" },
        )}`,
      }),
      invalidatesTags: [
        "Discovery Monitor Results",
        "Monitor Field Results",
        "Monitor Field Details",
      ],
    }),
    muteResource: build.mutation<any, ResourceActionQueryParams>({
      query: ({ staged_resource_urn }) => ({
        method: "POST",
        url: "/plus/discovery-monitor/mute",
        body: {
          staged_resource_urns: [staged_resource_urn],
        },
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
      invalidatesTags: [
        "Discovery Monitor Results",
        "Monitor Field Results",
        "Monitor Field Details",
      ],
    }),
    muteResources: build.mutation<any, BulkResourceActionQueryParams>({
      query: ({ staged_resource_urns }) => ({
        method: "POST",
        url: "/plus/discovery-monitor/mute",
        body: {
          staged_resource_urns,
        },
      }),
      invalidatesTags: [
        "Discovery Monitor Results",
        "Monitor Field Results",
        "Monitor Field Details",
      ],
    }),
    promoteResources: build.mutation<any, BulkResourceActionQueryParams>({
      query: ({ staged_resource_urns }) => ({
        method: "POST",
        url: `/plus/discovery-monitor/promote?${queryString.stringify(
          { staged_resource_urns },
          { arrayFormat: "none" },
        )}`,
      }),
      invalidatesTags: [
        "Discovery Monitor Results",
        "Monitor Field Results",
        "Monitor Field Details",
      ],
    }),
    updateResourceCategory: build.mutation<
      Array<{
        urn: string;
        data_uses?: string[] | null;
      }>,
      ChangeResourceCategoryQueryParam
    >({
      query: (params) => ({
        method: "PATCH",
        url: `/plus/discovery-monitor/${params.monitor_config_id}/results`,
        body: [
          {
            urn: params.staged_resource_urn,
            user_assigned_data_categories: params.user_assigned_data_categories,
            user_assigned_system_key: params.user_assigned_system_key,
          },
        ],
      }),

      invalidatesTags: [
        "Discovery Monitor Results",
        "Monitor Field Results",
        "Monitor Field Details",
      ],
    }),
    reviewStagedResources: build.mutation<
      any,
      BulkResourceActionQueryParams & {
        monitor_config_key: string;
      }
    >({
      query: ({ staged_resource_urns, monitor_config_key }) => ({
        method: "POST",
        url: `/plus/discovery-monitor/${monitor_config_key}/review`,
        body: {
          staged_resource_urns,
        },
      }),
      invalidatesTags: [
        "Discovery Monitor Results",
        "Monitor Field Results",
        "Monitor Field Details",
      ],
    }),
    // Identity Provider Monitor endpoints (Okta-specific)
    getIdentityProviderMonitorResults: build.query<
      Page_StagedResourceAPIResponse_,
      IdentityProviderMonitorResultsQueryParams
    >({
      query: ({ monitor_config_key, ...params }) => ({
        method: "GET",
        url: `/plus/identity-provider-monitors/${monitor_config_key}/results?${queryString.stringify(
          params,
          { arrayFormat: "none" },
        )}`,
      }),
      providesTags: () => ["Identity Provider Monitor Results"],
    }),
    getIdentityProviderMonitorFilters: build.query<
      IDPMonitorFiltersResponse,
      IdentityProviderMonitorFiltersQueryParams
    >({
      query: ({ monitor_config_key, ...params }) => ({
        method: "GET",
        url: `/plus/filters/idp_monitor_resources?${queryString.stringify(
          { monitor_config_id: monitor_config_key, ...params },
          { arrayFormat: "none" },
        )}`,
      }),
      providesTags: () => ["Identity Provider Monitor Filters"],
    }),
    executeIdentityProviderMonitor: build.mutation<
      { monitor_execution_id: string; task_id: string | null },
      IdentityProviderMonitorExecuteParams
    >({
      query: ({ monitor_config_key }) => ({
        method: "POST",
        url: `/plus/identity-provider-monitors/${monitor_config_key}/execute`,
      }),
      invalidatesTags: ["Discovery Monitor Configs"],
    }),
    promoteIdentityProviderMonitorResult: build.mutation<
      any,
      IdentityProviderResourceActionParam
    >({
      query: ({ monitor_config_key, urn }) => ({
        method: "POST",
        url: `/plus/identity-provider-monitors/${monitor_config_key}/results/${urn}/promote`,
      }),
      invalidatesTags: ["Identity Provider Monitor Results"],
    }),
    muteIdentityProviderMonitorResult: build.mutation<
      any,
      IdentityProviderResourceActionParam
    >({
      query: ({ monitor_config_key, urn }) => ({
        method: "POST",
        url: `/plus/identity-provider-monitors/${monitor_config_key}/results/bulk-mute`,
        body: [urn],
      }),
      invalidatesTags: ["Identity Provider Monitor Results"],
    }),
    unmuteIdentityProviderMonitorResult: build.mutation<
      any,
      IdentityProviderResourceActionParam
    >({
      query: ({ monitor_config_key, urn }) => ({
        method: "POST",
        url: `/plus/identity-provider-monitors/${monitor_config_key}/results/bulk-unmute`,
        body: [urn],
      }),
      invalidatesTags: ["Identity Provider Monitor Results"],
    }),
    updateInfrastructureSystemDataUses: build.mutation<
      Schema,
      { monitorId: string; urn: string; dataUses: string[] }
    >({
      query: (params) => ({
        method: "PATCH",
        url: `/plus/identity-provider-monitors/${params.monitorId}/results/${params.urn}`,
        body: {
          urn: params.urn,
          user_assigned_data_uses: params.dataUses,
        },
      }),
      invalidatesTags: ["Identity Provider Monitor Results"],
    }),
    bulkPromoteIdentityProviderMonitorResults: build.mutation<
      any,
      IdentityProviderResourceBulkActionParam
    >({
      query: ({ monitor_config_key, urns, bulkSelection }) => {
        // Backward compatibility: if urns is provided, use it
        if (urns && urns.length > 0) {
          return {
            method: "POST",
            url: `/plus/identity-provider-monitors/${monitor_config_key}/results/bulk-promote`,
            body: {
              urns,
            },
          };
        }
        // Otherwise use bulkSelection (filters-based)
        return {
          method: "POST",
          url: `/plus/identity-provider-monitors/${monitor_config_key}/results/bulk-promote`,
          body: bulkSelection || {},
        };
      },
      invalidatesTags: ["Identity Provider Monitor Results"],
    }),
    bulkMuteIdentityProviderMonitorResults: build.mutation<
      any,
      IdentityProviderResourceBulkActionParam
    >({
      query: ({ monitor_config_key, urns, bulkSelection }) => {
        // Backward compatibility: if urns is provided, use it
        if (urns && urns.length > 0) {
          return {
            method: "POST",
            url: `/plus/identity-provider-monitors/${monitor_config_key}/results/bulk-mute`,
            body: urns,
          };
        }
        // Otherwise use bulkSelection (filters-based)
        return {
          method: "POST",
          url: `/plus/identity-provider-monitors/${monitor_config_key}/results/bulk-mute`,
          body: bulkSelection || {},
        };
      },
      invalidatesTags: ["Identity Provider Monitor Results"],
    }),
    bulkUnmuteIdentityProviderMonitorResults: build.mutation<
      any,
      IdentityProviderResourceBulkActionParam
    >({
      query: ({ monitor_config_key, urns, bulkSelection }) => {
        // Backward compatibility: if urns is provided, use it
        if (urns && urns.length > 0) {
          return {
            method: "POST",
            url: `/plus/identity-provider-monitors/${monitor_config_key}/results/bulk-unmute`,
            body: urns,
          };
        }
        // Otherwise use bulkSelection (filters-based)
        return {
          method: "POST",
          url: `/plus/identity-provider-monitors/${monitor_config_key}/results/bulk-unmute`,
          body: bulkSelection || {},
        };
      },
      invalidatesTags: ["Identity Provider Monitor Results"],
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
  useUnmuteResourcesMutation,
  useUpdateResourceCategoryMutation,
  useReviewStagedResourcesMutation,
  useGetIdentityProviderMonitorResultsQuery,
  useGetIdentityProviderMonitorFiltersQuery,
  useExecuteIdentityProviderMonitorMutation,
  usePromoteIdentityProviderMonitorResultMutation,
  useMuteIdentityProviderMonitorResultMutation,
  useUnmuteIdentityProviderMonitorResultMutation,
  useUpdateInfrastructureSystemDataUsesMutation,
  useBulkPromoteIdentityProviderMonitorResultsMutation,
  useBulkMuteIdentityProviderMonitorResultsMutation,
  useBulkUnmuteIdentityProviderMonitorResultsMutation,
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
