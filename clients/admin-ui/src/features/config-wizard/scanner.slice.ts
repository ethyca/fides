import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import { ScannerGenerateParams, ScannerGenerateResponse } from "./types";

export const scannerApi = createApi({
  reducerPath: "scannerApi",
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_FIDESCTL_API,
  }),
  endpoints: (build) => ({
    generate: build.mutation<ScannerGenerateResponse, ScannerGenerateParams>({
      query: (body) => ({
        url: `generate/`,
        method: "POST",
        body,
      }),
    }),
  }),
});

export const { useGenerateMutation } = scannerApi;
