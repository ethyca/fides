import { BaseQueryFn, createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { getPrivacyCenterEnvironment } from "~/app/server-environment";
import { addCommonHeaders } from "~/common/CommonHeaders";


// Thin wrapper around fetchBaseQuery() to allow us to inject the configurable baseUrl at runtime
const baseApiQueryFn: BaseQueryFn = async (args, api, extraOptions) => {
  const environment = getPrivacyCenterEnvironment();
  const baseQuery = fetchBaseQuery({
    baseUrl: environment.fidesApiUrl,
    prepareHeaders: (headers) => addCommonHeaders(headers),
  });
  return baseQuery(args, api, extraOptions);
}

/**
 * Uses the code splitting pattern. New endpoints should be injected into this base API which
 * itself has an empty endpoint object.
 *
 * https://redux-toolkit.js.org/rtk-query/api/created-api/code-splitting#injectendpoints
 */
export const baseApi = createApi({
  reducerPath: "baseApi",
  baseQuery: baseApiQueryFn,
  tagTypes: [],
  endpoints: () => ({}),
});
