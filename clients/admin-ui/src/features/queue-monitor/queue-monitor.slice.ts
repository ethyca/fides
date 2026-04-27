import { baseApi } from "~/features/common/api.slice";

import { QueueMonitorResponse } from "./types";

export const queueMonitorApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getQueueMonitor: build.query<QueueMonitorResponse, void>({
      query: () => ({
        url: "/queue-monitor",
        method: "GET",
      }),
      providesTags: ["Queue Monitor"],
    }),
  }),
});

export const { useGetQueueMonitorQuery } = queueMonitorApi;
