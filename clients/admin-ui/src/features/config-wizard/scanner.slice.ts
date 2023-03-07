import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { RootState } from "~/app/store";
import { selectToken } from "~/features/auth";
import { addCommonHeaders } from "~/features/common/CommonHeaders";
import { GenerateRequestPayload, GenerateResponse } from "~/types/api";

export const scannerApi = createApi({
  reducerPath: "scannerApi",
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_FIDESCTL_API,
    prepareHeaders: (headers, { getState }) => {
      const token: string | null = selectToken(getState() as RootState);
      addCommonHeaders(headers, token);
      return headers;
    },
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
