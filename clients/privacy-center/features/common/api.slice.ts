import {
  BaseQueryFn,
  createApi,
  fetchBaseQuery,
} from "@reduxjs/toolkit/query/react";

import type { RootState } from "~/app/store";
import { addCommonHeaders } from "~/common/CommonHeaders";
import { selectSettings } from "~/features/common/settings.slice";

/**
 * Thin wrapper around fetchBaseQuery() to allow us to inject the configurable baseUrl at runtime
 * (https://redux-toolkit.js.org/rtk-query/usage/customizing-queries#constructing-a-dynamic-base-url-using-redux-state)
 */
const dynamicBaseQuery: BaseQueryFn = async (args, api, extraOptions) => {
  const settingsState = selectSettings(api.getState() as RootState);
  if (settingsState?.settings?.FIDES_API_URL) {
    const baseQuery = fetchBaseQuery({
      baseUrl: settingsState.settings.FIDES_API_URL,
      prepareHeaders: (headers) => addCommonHeaders(headers),
    });
    return baseQuery(args, api, extraOptions);
  }
  throw new Error("Unable to query Fides API, missing FIDES_API_URL!");
};

/**
 * Uses the code splitting pattern. New endpoints should be injected into this base API which
 * itself has an empty endpoint object.
 *
 * https://redux-toolkit.js.org/rtk-query/api/created-api/code-splitting#injectendpoints
 */
export const baseApi = createApi({
  reducerPath: "baseApi",
  baseQuery: dynamicBaseQuery,
  tagTypes: ["Privacy Experience"],
  endpoints: () => ({}),
});
