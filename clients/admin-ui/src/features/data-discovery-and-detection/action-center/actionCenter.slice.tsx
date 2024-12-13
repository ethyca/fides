import { baseApi } from "~/features/common/api.slice";

import { MonitorSummaryPaginatedResponse } from "./types";

const actionCenterApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getMonitorSummary: build.query<
      MonitorSummaryPaginatedResponse,
      {
        pageIndex?: number;
        pageSize?: number;
        search?: string;
      }
    >({
      query: ({ pageIndex = 1, pageSize = 20, search }) => ({
        url: `/plus/discovery-monitor/results`,
        params: { page: pageIndex, size: pageSize, search },
      }),
      providesTags: ["Monitor Summary"],
    }),
  }),
});

export const { useGetMonitorSummaryQuery } = actionCenterApi;
