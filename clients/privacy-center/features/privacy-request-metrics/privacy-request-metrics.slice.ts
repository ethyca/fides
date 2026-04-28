import { baseApi } from "~/features/common/api.slice";

import type { PrivacyRequestMetricsResponse } from "./types";

export const privacyRequestMetricsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getPrivacyRequestMetrics: build.query<PrivacyRequestMetricsResponse, void>({
      query: () => ({
        url: `plus/privacy-request-metrics`,
      }),
    }),
  }),
});

export const { useGetPrivacyRequestMetricsQuery } = privacyRequestMetricsApi;
