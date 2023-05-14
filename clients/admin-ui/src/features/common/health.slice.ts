import { createSelector } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { RootState } from "~/app/store";
import { selectToken } from "~/features/auth";
import { addCommonHeaders } from "~/features/common/CommonHeaders";
import { CoreHealthCheck } from "~/types/api";

/**
 * Note: this one does not extend from baseApi because the health endpoint is
 * not nested under /api/v1
 */
export const healthApi = createApi({
  reducerPath: "healthApi",
  baseQuery: fetchBaseQuery({
    baseUrl: `/`,
    prepareHeaders: (headers, { getState }) => {
      const token: string | null = selectToken(getState() as RootState);
      addCommonHeaders(headers, token);
      return headers;
    },
  }),
  tagTypes: ["Health"],
  endpoints: (build) => ({
    getHealth: build.query<CoreHealthCheck, void>({
      query: () => "health",
    }),
  }),
});

export const { useGetHealthQuery } = healthApi;

export const selectHealth: (state: RootState) => CoreHealthCheck | undefined =
  createSelector(healthApi.endpoints.getHealth.select(), ({ data }) => data);
