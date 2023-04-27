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
    "AllowList",
    "Auth",
    "ClassifyInstancesDatasets",
    "ClassifyInstancesSystems",
    "Connection Type",
    "CustomFieldDefinition",
    "CustomFields",
    "Data Categories",
    "Datamap",
    "Data Subjects",
    "Data Qualifiers",
    "Data Uses",
    "DatastoreConnection",
    "Dataset",
    "Datasets",
    "LatestScan",
    "Managed Systems",
    "Notification",
    "Organization",
    "Plus",
    "PrivacyNotices",
    "System",
    "Request",
    "Roles",
    "User",
  ],
  endpoints: () => ({}),
});
