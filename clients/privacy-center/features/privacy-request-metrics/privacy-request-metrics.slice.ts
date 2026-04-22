import { baseApi } from "~/features/common/api.slice";

import type { PrivacyRequestMetricsResponse } from "./types";

export const privacyRequestMetricsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getPrivacyRequestMetrics: build.query<
      PrivacyRequestMetricsResponse,
      { location?: string } | void
    >({
      query: (params) => ({
        url: `plus/privacy-request-metrics`,
        params: params || undefined,
      }),
    }),
  }),
});

export const { useGetPrivacyRequestMetricsQuery } = privacyRequestMetricsApi;
