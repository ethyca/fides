import { baseApi } from "~/features/common/api.slice";

export interface QueryLogConfigResponse {
  key: string;
  name: string;
  connection_config_key: string;
  enabled: boolean;
  poll_interval_seconds: number;
  created_at: string;
  updated_at: string;
}

export interface QueryLogConfigListResponse {
  items: QueryLogConfigResponse[];
  total: number;
  page: number;
  size: number;
}

export interface GetQueryLogConfigsParams {
  page?: number;
  size?: number;
  connection_config_key?: string;
}

export interface CreateQueryLogConfigRequest {
  connection_config_key: string;
  name: string;
  key?: string;
  enabled?: boolean;
  poll_interval_seconds?: number;
}

export interface UpdateQueryLogConfigRequest {
  configKey: string;
  name?: string;
  enabled?: boolean;
  poll_interval_seconds?: number;
}

export interface TestQueryLogConnectionResponse {
  success: boolean;
  message: string;
}

export interface TriggerQueryLogPollResponse {
  entries_processed: number;
  message?: string;
}

const queryLogConfigApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getQueryLogConfigs: build.query<
      QueryLogConfigListResponse,
      GetQueryLogConfigsParams
    >({
      query: (params) => ({
        url: "query-log-config",
        method: "GET",
        params,
      }),
      providesTags: ["QueryLogConfig"],
    }),

    getQueryLogConfigByKey: build.query<QueryLogConfigResponse, string>({
      query: (configKey) => ({
        url: `query-log-config/${configKey}`,
        method: "GET",
      }),
      providesTags: (_result, _error, configKey) => [
        { type: "QueryLogConfig", id: configKey },
      ],
    }),

    createQueryLogConfig: build.mutation<
      QueryLogConfigResponse,
      CreateQueryLogConfigRequest
    >({
      query: (body) => ({
        url: "query-log-config",
        method: "POST",
        body,
      }),
      invalidatesTags: ["QueryLogConfig"],
    }),

    updateQueryLogConfig: build.mutation<
      QueryLogConfigResponse,
      UpdateQueryLogConfigRequest
    >({
      query: ({ configKey, ...body }) => ({
        url: `query-log-config/${configKey}`,
        method: "PUT",
        body,
      }),
      invalidatesTags: ["QueryLogConfig"],
    }),

    deleteQueryLogConfig: build.mutation<void, string>({
      query: (configKey) => ({
        url: `query-log-config/${configKey}`,
        method: "DELETE",
      }),
      invalidatesTags: ["QueryLogConfig"],
    }),

    testQueryLogConnection: build.mutation<
      TestQueryLogConnectionResponse,
      string
    >({
      query: (configKey) => ({
        url: `query-log-config/${configKey}/test`,
        method: "POST",
      }),
    }),

    triggerQueryLogPoll: build.mutation<TriggerQueryLogPollResponse, string>({
      query: (configKey) => ({
        url: `query-log-config/${configKey}/poll`,
        method: "POST",
      }),
      invalidatesTags: ["QueryLogConfig"],
    }),
  }),
});

export const {
  useGetQueryLogConfigsQuery,
  useGetQueryLogConfigByKeyQuery,
  useCreateQueryLogConfigMutation,
  useUpdateQueryLogConfigMutation,
  useDeleteQueryLogConfigMutation,
  useTestQueryLogConnectionMutation,
  useTriggerQueryLogPollMutation,
} = queryLogConfigApi;
