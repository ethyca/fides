// import { createSelector } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { type } from "os";

import type { RootState } from "~/app/store";
import { selectToken } from "~/features/auth";
import { addCommonHeaders } from "~/features/common/CommonHeaders";

type Stats = {
  instance_id: string;
  stats: Record<string, string>;
};

type Scan = {
  file_url: string;
  raw_file_url: string;
  contains_pii: boolean;
  handles_pii: boolean;
  pii_occurances: string[];
  pii_handling: string[];
  finding_urls: Record<string, string>[];
};
/**
 * Note: this one does not extend from baseApi because the health endpoint is
 * not nested under /api/v1
 */
export const scanCodebaseApi = createApi({
  reducerPath: "scanCodebaseApi",
  baseQuery: fetchBaseQuery({
    baseUrl: `http://localhost:8081/api/v1/`,
  }),
  tagTypes: ["ScanCodebase"],
  endpoints: (build) => ({
    getScanStats: build.query<Stats, { url: string }>({
      query: ({ url }) => ({ url: `stats` }),
      providesTags: ["ScanCodebase"],
    }),
    getScanPii: build.query<Scan[], { id: string }>({
      query: ({ id }) => `scan/${id}`,
    }),
  }),
});

export const { useLazyGetScanPiiQuery, useLazyGetScanStatsQuery } =
  scanCodebaseApi;

// export const selectScanCodebase: (state: RootState) => any | undefined =
//   createSelector(scanCodebaseApi.endpoints.getScanCodebase.select(), ({ data }) => data);
