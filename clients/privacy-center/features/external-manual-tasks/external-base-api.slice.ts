/**
 * External Base API Configuration
 *
 * Separated from store.ts to avoid circular dependencies
 * FIXES: Authentication token issue where privacy-center baseApi didn't know about external auth tokens
 */

import {
  BaseQueryFn,
  createApi,
  fetchBaseQuery,
} from "@reduxjs/toolkit/query/react";

import { addCommonHeaders } from "~/common/CommonHeaders";

import { selectExternalToken } from "./external-auth.slice";

// Define the external root state type for the base query
interface ExternalRootState {
  externalAuth: {
    token: string | null;
    isAuthenticated: boolean;
    user: any;
    emailToken: string | null;
    isLoading: boolean;
    error: string | null;
  };
  settings: {
    settings: {
      FIDES_API_URL?: string;
    } | null;
  };
  config: any;
  externalManualTasks: any;
}

/**
 * Custom base query for external store that handles external authentication
 * FIXES: The privacy-center baseApi doesn't know about external auth tokens
 */
const externalDynamicBaseQuery: BaseQueryFn = async (
  args,
  api,
  extraOptions,
) => {
  const state = api.getState() as ExternalRootState;

  // Get settings from external store
  const settingsState = state.settings;
  if (settingsState?.settings?.FIDES_API_URL) {
    // Get external auth token from external store
    const authToken = selectExternalToken({ externalAuth: state.externalAuth });

    const isMultipart =
      typeof args === "object" &&
      args !== null &&
      (args as any).body instanceof FormData;

    const baseQuery = fetchBaseQuery({
      baseUrl: settingsState.settings.FIDES_API_URL,
      prepareHeaders: (headers) => {
        addCommonHeaders(headers, authToken);
        // If the request uses FormData, ensure we don't override the browser-set multipart header
        if (isMultipart) {
          headers.delete("Content-Type");
        }
        return headers;
      },
    });
    return baseQuery(args, api, extraOptions);
  }
  throw new Error("Unable to query Fides API, missing FIDES_API_URL!");
};

/**
 * External base API with proper authentication handling
 * SEPARATE from privacy-center baseApi to avoid token conflicts
 */
export const externalBaseApi = createApi({
  reducerPath: "externalBaseApi",
  baseQuery: externalDynamicBaseQuery,
  tagTypes: ["External Manual Tasks"],
  endpoints: () => ({}),
});
