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
    "Catalog Systems",
    "Catalog Projects",
    "Classify Instances Datasets",
    "Classify Instances Systems",
    "Connection Type",
    "Consentable Items",
    "Consent Reporting",
    "Consent Reporting Export",
    "Country Locations",
    "Current Privacy Preferences",
    "Custom Assets",
    "Custom Field Definition",
    "Custom Fields",
    "Custom Reports",
    "Data Categories",
    "Datamap",
    "Data Subjects",
    "Data Uses",
    "Datastore Connection",
    "Dataset",
    "Datasets",
    "Discovery Monitor Configs",
    "Discovery Monitor Results",
    "Email Invite Status",
    "Fides Cloud Config",
    "Languages",
    "Locations",
    "Manual Fields",
    "Manual Tasks",
    "Messaging Templates",
    "Dictionary",
    "System Vendors",
    "Latest Scan",
    "Managed Systems",
    "Notification",
    "Organization",
    "Plus",
    "Policies",
    "Privacy Experience Configs",
    "Experience Config Translations",
    "Privacy Notices",
    "Privacy Notice Translations",
    "Privacy Request Attachments",
    "Privacy Request Comments",
    "Property",
    "Property-Specific Messaging Templates",
    "Purpose",
    "Shared Monitor Configs",
    "System",
    "System Assets",
    "System History",
    "Request",
    "Roles",
    "User",
    "Configuration Settings",
    "TCF Purpose Override",
    "OpenID Provider",
  ],
  endpoints: () => ({}),
});
