import { baseApi } from "~/features/common/api.slice";

import type { PrivacyRequestMetricsResponse } from "./types";

interface PrivacyRequestMetricsParams {
  start_date: string;
  end_date: string;
  location?: string;
}

export const privacyRequestMetricsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getPrivacyRequestMetrics: build.query<
      PrivacyRequestMetricsResponse,
      PrivacyRequestMetricsParams
    >({
      query: (params) => ({
        url: `plus/privacy-request-metrics`,
        params,
      }),
    }),
  }),
});

export const { useGetPrivacyRequestMetricsQuery } = privacyRequestMetricsApi;
