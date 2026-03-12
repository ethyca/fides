import { baseApi } from "~/features/common/api.slice";

import type {
  DataConsumerRequestsResponse,
  DataConsumersByViolationsResponse,
  PaginatedResponse,
  PolicyViolationAggregate,
  PolicyViolationLog,
} from "./types";

interface DataConsumerRequestsParams {
  start_date: string;
  end_date: string;
  policy?: string;
  data_uses?: string[];
}

interface DataConsumersByViolationsParams {
  start_date: string;
  end_date: string;
  group_by: "consumer";
  order_by?: "violation_count" | "request_count";
}

interface PaginatedParams {
  page?: number;
  size?: number;
}

interface PolicyViolationsParams extends PaginatedParams {
  policy?: string;
  control?: string;
  sort_by?: "violation_count" | "last_violation";
  sort_direction?: "asc" | "desc";
}

const accessControlApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getDataConsumerRequests: build.query<
      DataConsumerRequestsResponse,
      DataConsumerRequestsParams
    >({
      query: (params) => ({
        url: "data-consumer/requests",
        params,
      }),
      providesTags: ["Access Control"],
    }),

    getDataConsumersByViolations: build.query<
      DataConsumersByViolationsResponse,
      DataConsumersByViolationsParams
    >({
      query: (params) => ({
        url: "data-consumer/requests",
        params,
      }),
      providesTags: ["Access Control"],
    }),

    getPolicyViolations: build.query<
      PaginatedResponse<PolicyViolationAggregate>,
      PolicyViolationsParams
    >({
      query: (params) => ({
        url: "policy/violations",
        params,
      }),
      providesTags: ["Access Control"],
    }),

    getPolicyViolationLogs: build.query<
      PaginatedResponse<PolicyViolationLog>,
      PaginatedParams
    >({
      query: (params) => ({
        url: "policy/violations/logs",
        params,
      }),
      providesTags: ["Access Control"],
    }),
  }),
});

export const {
  useGetDataConsumerRequestsQuery,
  useGetDataConsumersByViolationsQuery,
  useGetPolicyViolationsQuery,
  useGetPolicyViolationLogsQuery,
} = accessControlApi;
