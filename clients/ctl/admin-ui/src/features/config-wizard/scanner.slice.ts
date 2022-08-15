import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import { GenerateRequestPayload, GenerateResponse } from "~/types/api";

export const scannerApi = createApi({
  reducerPath: "scannerApi",
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_FIDESCTL_API,
  }),
  endpoints: (build) => ({
    generate: build.mutation<GenerateResponse, GenerateRequestPayload>({
      query: (body) => ({
        url: `generate`,
        method: "POST",
        body,
      }),
    }),
  }),
});

export const { useGenerateMutation } = scannerApi;
