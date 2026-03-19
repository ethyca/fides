import { baseApi } from "~/features/common/api.slice";

import type {
  AccessControlSummaryResponse,
  ConsumerRequestsByConsumerResponse,
  CursorPaginatedViolationLogs,
  FiltersResponse,
  PaginatedResponse,
  PolicyViolationAggregate,
  PolicyViolationLog,
  TimeseriesResponse,
} from "./types";

interface TimeseriesParams {
  start_date: string;
  end_date: string;
  consumer?: string | string[];
  policy?: string | string[];
  dataset?: string | string[];
  data_use?: string | string[];
}

interface ConsumersByViolationsParams {
  start_date: string;
  end_date: string;
  consumer?: string | string[];
  policy?: string | string[];
  dataset?: string | string[];
  data_use?: string | string[];
  order_by?: "violation_count" | "request_count";
}

interface SummaryParams {
  start_date?: string;
  end_date?: string;
}

interface PaginatedParams {
  page?: number;
  size?: number;
}

interface ViolationLogsParams {
  cursor?: string | null;
  size?: number;
  consumer?: string | string[];
  policy?: string | string[];
  dataset?: string | string[];
  data_use?: string | string[];
  start_date?: string;
  end_date?: string;
}

interface PolicyViolationsParams extends PaginatedParams {
  policy?: string | string[];
  control?: string | string[];
  sort_by?: "violation_count" | "last_violation";
  sort_direction?: "asc" | "desc";
  start_date?: string;
  end_date?: string;
}

interface FiltersParams {
  start_date?: string;
  end_date?: string;
  consumer?: string | string[];
  policy?: string | string[];
  dataset?: string | string[];
  data_use?: string | string[];
}

const accessControlApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAccessControlSummary: build.query<
      AccessControlSummaryResponse,
      SummaryParams
    >({
      query: (params) => ({
        url: "access-control/summary",
        params,
      }),
      providesTags: ["Access Control"],
    }),

    getRequestsTimeseries: build.query<TimeseriesResponse, TimeseriesParams>({
      query: (params) => ({
        url: "access-control/requests",
        params,
      }),
      providesTags: ["Access Control"],
    }),

    getConsumersByViolations: build.query<
      ConsumerRequestsByConsumerResponse,
      ConsumersByViolationsParams
    >({
      query: (params) => ({
        url: "access-control/consumers",
        params,
      }),
      providesTags: ["Access Control"],
    }),

    getPolicyViolations: build.query<
      PaginatedResponse<PolicyViolationAggregate>,
      PolicyViolationsParams
    >({
      query: (params) => ({
        url: "access-control/violations",
        params,
      }),
      providesTags: ["Access Control"],
    }),

    getViolationLogs: build.query<
      CursorPaginatedViolationLogs,
      ViolationLogsParams
    >({
      query: ({ cursor, ...rest }) => ({
        url: "access-control/violations/logs",
        params: {
          ...rest,
          ...(cursor ? { cursor } : {}),
        },
      }),
      providesTags: ["Access Control"],
    }),

    getViolationDetail: build.query<PolicyViolationLog, string>({
      query: (id) => ({
        url: `access-control/violations/${id}`,
      }),
      providesTags: ["Access Control"],
    }),

    getFilters: build.query<FiltersResponse, FiltersParams | void>({
      query: (params) => ({
        url: "access-control/filters",
        params: params ?? undefined,
      }),
      providesTags: ["Access Control"],
    }),
  }),
});

export const {
  useGetAccessControlSummaryQuery,
  useGetRequestsTimeseriesQuery,
  useGetConsumersByViolationsQuery,
  useGetPolicyViolationsQuery,
  useGetViolationLogsQuery,
  useGetViolationDetailQuery,
  useGetFiltersQuery,
} = accessControlApi;
