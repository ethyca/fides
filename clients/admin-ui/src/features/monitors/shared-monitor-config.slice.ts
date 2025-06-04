import { baseApi } from "~/features/common/api.slice";
import { Page_SharedMonitorConfig_ } from "~/types/api/models/Page_SharedMonitorConfig_";
import { SharedMonitorConfig } from "~/types/api/models/SharedMonitorConfig";
import { PaginationQueryParams } from "~/types/common/PaginationQueryParams";

interface SharedMonitorConfigQueryParams extends PaginationQueryParams {}

const sharedMonitorConfigApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getSharedMonitorConfigs: build.query<
      Page_SharedMonitorConfig_,
      SharedMonitorConfigQueryParams
    >({
      query: (params) => ({
        method: "GET",
        url: "/plus/shared-monitor-config",
        params,
      }),
      providesTags: ["Shared Monitor Configs"],
    }),
    getSharedMonitorConfigById: build.query<
      SharedMonitorConfig,
      { id: string }
    >({
      query: ({ id }) => ({
        method: "GET",
        url: `/plus/shared-monitor-config/${id}`,
      }),
      providesTags: ["Shared Monitor Configs"],
    }),
    createSharedMonitorConfig: build.mutation<
      SharedMonitorConfig,
      SharedMonitorConfig
    >({
      query: (body) => ({
        method: "POST",
        url: "/plus/shared-monitor-config",
        body,
      }),
      invalidatesTags: ["Shared Monitor Configs"],
    }),
    updateSharedMonitorConfig: build.mutation<
      SharedMonitorConfig,
      SharedMonitorConfig
    >({
      query: (body) => ({
        method: "PUT",
        url: `/plus/shared-monitor-config/${body.id}`,
        body,
      }),
      invalidatesTags: ["Shared Monitor Configs"],
    }),
    deleteSharedMonitorConfig: build.mutation<void, { id: string }>({
      query: ({ id }) => ({
        method: "DELETE",
        url: `/plus/shared-monitor-config/${id}`,
      }),
      invalidatesTags: ["Shared Monitor Configs"],
    }),
  }),
});

export const {
  useGetSharedMonitorConfigsQuery,
  useGetSharedMonitorConfigByIdQuery,
  useCreateSharedMonitorConfigMutation,
  useUpdateSharedMonitorConfigMutation,
  useDeleteSharedMonitorConfigMutation,
} = sharedMonitorConfigApi;
