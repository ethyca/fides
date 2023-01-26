import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { addCommonHeaders } from "~/common/CommonHeaders";
import { hostUrl } from "~/constants";

/**
 * Uses the code splitting pattern. New endpoints should be injected into this base API which
 * itself has an empty endpoint object.
 *
 * https://redux-toolkit.js.org/rtk-query/api/created-api/code-splitting#injectendpoints
 */
export const baseApi = createApi({
  reducerPath: "baseApi",
  baseQuery: fetchBaseQuery({
    baseUrl: hostUrl,
    prepareHeaders: (headers) => addCommonHeaders(headers),
  }),
  tagTypes: [],
  endpoints: () => ({}),
});
