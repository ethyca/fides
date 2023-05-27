import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { RootState } from "~/app/store";

import { addCommonHeaders } from "./CommonHeaders";

// Uses the code splitting pattern. New endpoints should be injected into this base API
// which itself has an empty endpoint object.
export const baseApi = createApi({
  reducerPath: "baseApi",
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_FIDESCTL_API,
    prepareHeaders: (headers, { getState }) => {
      const { token } = (getState() as RootState).auth;
      addCommonHeaders(headers, token);
      return headers;
    },
  }),
  tagTypes: [
    "Allow List",
    "Auth",
    "Classify Instances Datasets",
    "Classify Instances Systems",
    "Connection Type",
    "Custom Field Definition",
    "Custom Fields",
    "Data Categories",
    "Datamap",
    "Data Subjects",
    "Data Qualifiers",
    "Data Uses",
    "Datastore Connection",
    "Dataset",
    "Datasets",
    "Latest Scan",
    "Managed Systems",
    "Notification",
    "Organization",
    "Plus",
    "Privacy Experience Configs",
    "Privacy Notices",
    "System",
    "Request",
    "Roles",
    "User",
  ],
  endpoints: () => ({}),
});
