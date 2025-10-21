import { baseApi } from "~/features/common/api.slice";
import {
  buildArrayQueryParams,
  getQueryParamsFromArray,
} from "~/features/common/utils";
import {
  ConnectionType,
  ConsentStatus,
  DiffStatus,
  MonitorConfig,
  MonitorTaskInProgressResponse,
  Page_ConsentBreakdown_,
  Page_StagedResourceAPIResponse_,
  Page_SystemStagedResourcesAggregateRecord_,
  PromoteResourcesResponse,
  Schema,
  StagedResourceAPIResponse,
  WebsiteMonitorResourcesFilters,
} from "~/types/api";
import { BaseStagedResourcesRequest } from "~/types/api/models/BaseStagedResourcesRequest";
import { ClassifyResourcesResponse } from "~/types/api/models/ClassifyResourcesResponse";
import { DatastoreMonitorResourcesDynamicFilters } from "~/types/api/models/DatastoreMonitorResourcesDynamicFilters";
import { ExecutionLogStatus } from "~/types/api/models/ExecutionLogStatus";
import { Page_DatastoreStagedResourceTreeAPIResponse_ } from "~/types/api/models/Page_DatastoreStagedResourceTreeAPIResponse_";
import {
  PaginatedResponse,
  PaginationQueryParams,
  SearchQueryParams,
  SortQueryParams,
} from "~/types/query-params";

import { DiscoveredAssetsColumnKeys } from "./constants";
import {
  MonitorAggregatedResults,
  MonitorSummaryPaginatedResponse,
} from "./types";
import { getMonitorType } from "./utils/getMonitorType";

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
      transformResponse: (
        response: PaginatedResponse<MonitorAggregatedResults>,
      ) => ({
        ...response,
        items: response.items.map((monitor) => ({
          ...monitor,
          monitorType: getMonitorType(monitor.connection_type),
          isTestMonitor:
            monitor.connection_type === ConnectionType.TEST_WEBSITE ||
            monitor.connection_type === ConnectionType.FIDES,
        })),
      }),
      providesTags: ["Discovery Monitor Results"],
    }),
    getMonitorConfig: build.query<
      MonitorConfig,
      {
        monitor_config_id: string;
      }
    >({
      query: ({ monitor_config_id }) => ({
        url: `/plus/discovery-monitor/${monitor_config_id}`,
      }),
    }),
    getDatastoreFilters: build.query<
      DatastoreMonitorResourcesDynamicFilters,
      {
        monitor_config_id: string;
      }
    >({
      query: ({ monitor_config_id }) => ({
        url: `/plus/filters/datastore_monitor_resources?monitor_config_id=${monitor_config_id}`,
      }),
    }),

    getMonitorTree: build.query<
      Page_DatastoreStagedResourceTreeAPIResponse_,
      Partial<PaginationQueryParams> & {
        monitor_config_id: string;
        staged_resource_urn?: string;
        include_descendant_details?: boolean;
      }
    >({
      query: ({
        page = 1,
        size = 20,
        monitor_config_id,
        staged_resource_urn,
        include_descendant_details,
      }) => ({
        url: `/plus/discovery-monitor/${monitor_config_id}/tree`,
        params: { staged_resource_urn, include_descendant_details, page, size },
      }),
    }),
    getDiscoveredSystemAggregate: build.query<
      Page_SystemStagedResourcesAggregateRecord_,
      {
        key: string;
        resolved_system_id?: string;
        diff_status?: DiffStatus[];
      } & SearchQueryParams &
        PaginationQueryParams
    >({
      query: ({
        key,
        resolved_system_id,
        page = 1,
        size = 20,
        search,
        diff_status,
      }) => ({
        url: `/plus/discovery-monitor/system-aggregate-results`,
        params: {
          monitor_config_id: key,
          resolved_system_id,
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
        sort_by = [DiscoveredAssetsColumnKeys.NAME],
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
        return {
          method: "POST",
          url: `/plus/discovery-monitor/mute`,
          body: {
            staged_resource_urns: params.urnList,
          },
        };
      },
      invalidatesTags: ["Discovery Monitor Results", "Monitor Field Results"],
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
        statuses: ConsentStatus[];
      } & PaginationQueryParams
    >({
      query: ({ stagedResourceUrn, statuses, page = 1, size = 20 }) => {
        const params = new URLSearchParams();

        // Add pagination params
        params.append("page", String(page));
        params.append("size", String(size));

        // Add status array params
        statuses.forEach((status) => {
          params.append("status", status);
        });

        return {
          url: `/plus/discovery-monitor/staged_resource/${encodeURIComponent(
            stagedResourceUrn,
          )}/consent`,
          params,
        };
      },
    }),
    getWebsiteMonitorResourceFilters: build.query<
      WebsiteMonitorResourcesFilters,
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
    getInProgressMonitorTasks: build.query<
      {
        items: MonitorTaskInProgressResponse[];
        total: number;
        page: number;
        pages: number;
        size: number;
      },
      SearchQueryParams &
        PaginationQueryParams & {
          task_types?: string[];
          statuses?: ExecutionLogStatus[];
          return_dismissed?: boolean;
        }
    >({
      query: ({
        page = 1,
        size = 20,
        search,
        task_types,
        statuses,
        return_dismissed = false,
      }) => {
        const params = new URLSearchParams({
          page: page.toString(),
          size: size.toString(),
          return_dismissed: return_dismissed.toString(),
        });

        if (search) {
          params.append("search", search);
        }

        if (task_types?.length) {
          task_types.forEach((type) => params.append("action_type", type));
        }

        if (statuses?.length) {
          statuses.forEach((status) => params.append("status", status));
        }

        return {
          url: `/plus/discovery-monitor/tasks?${params.toString()}`,
        };
      },
      providesTags: ["Monitor Tasks"],
    }),
    retryMonitorTask: build.mutation<
      {
        id: string;
        monitor_config_id: string;
        action_type: string;
        status: string;
        celery_id: string;
      },
      { taskId: string }
    >({
      query: ({ taskId }) => ({
        url: `/plus/discovery-monitor/tasks/${taskId}/retry`,
        method: "POST",
      }),
      invalidatesTags: ["Monitor Tasks"],
    }),
    dismissMonitorTask: build.mutation<
      MonitorTaskInProgressResponse,
      { taskId: string }
    >({
      query: ({ taskId }) => ({
        url: `/plus/discovery-monitor/tasks/${taskId}/dismissed`,
        method: "POST",
      }),
      invalidatesTags: ["Monitor Tasks"],
    }),
    undismissMonitorTask: build.mutation<
      MonitorTaskInProgressResponse,
      { taskId: string }
    >({
      query: ({ taskId }) => ({
        url: `/plus/discovery-monitor/tasks/${taskId}/dismissed`,
        method: "DELETE",
      }),
      invalidatesTags: ["Monitor Tasks"],
    }),
    classifyStagedResources: build.mutation<
      ClassifyResourcesResponse,
      BaseStagedResourcesRequest & { monitor_config_key: string }
    >({
      query: ({ monitor_config_key, ...body }) => ({
        url: `/plus/discovery-monitor/${monitor_config_key}/classify`,
        method: "POST",
        body,
      }),
      invalidatesTags: ["Monitor Field Results"],
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
  useGetInProgressMonitorTasksQuery,
  useRetryMonitorTaskMutation,
  useDismissMonitorTaskMutation,
  useUndismissMonitorTaskMutation,
  useGetMonitorTreeQuery,
  useLazyGetMonitorTreeQuery,
  useGetMonitorConfigQuery,
  useGetDatastoreFiltersQuery,
  useClassifyStagedResourcesMutation,
} = actionCenterApi;
