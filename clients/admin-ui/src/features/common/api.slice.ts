import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { RootState } from "~/app/store";
import { selectToken } from "~/features/auth";

import { addCommonHeaders } from "./CommonHeaders";

// Uses the code splitting pattern. New endpoints should be injected into this base API
// which itself has an empty endpoint object.
export const baseApi = createApi({
  reducerPath: "baseApi",
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_FIDESCTL_API,
    prepareHeaders: (headers, { getState }) => {
      const token: string | null = selectToken(getState() as RootState);
      addCommonHeaders(headers, token);
      return headers;
    },
  }),
  tagTypes: ["DatastoreConnection", "Dataset", "Datasets"],
  endpoints: () => ({}),
});
