import { baseApi } from "~/features/common/api.slice";
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
  }),
});

export const {
  useGetAggregateMonitorResultsQuery,
  useGetDiscoveredSystemAggregateQuery,
} = actionCenterApi;
