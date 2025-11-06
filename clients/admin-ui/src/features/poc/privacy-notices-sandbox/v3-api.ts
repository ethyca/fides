import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { RootState } from "~/app/store";
import { addCommonHeaders } from "~/features/common/CommonHeaders";
import { baseApi } from "~/features/common/api.slice";
import type { Page_Union_PrivacyExperienceResponse__TCFBannerExperienceMinimalResponse__ } from "~/types/api";

export interface PrivacyExperienceQueryParams {
  region: string;
  show_disabled: boolean;
  component: string;
  systems_applicable: boolean;
}

// V3 API Types
export interface ConsentPreferenceCreate {
  notice_key: string;
  notice_history_id: string;
  value: "opt_in" | "opt_out" | "acknowledge";
  experience_config_history_id?: string | null;
  meta?: Record<string, any> | null;
}

export interface ConsentCreate {
  identity: {
    email?: { value: string };
    phone_number?: { value: string };
    fides_user_device_id?: { value: string };
    external_id?: { value: string };
  };
  preferences: ConsentPreferenceCreate[];
  scope?: {
    property_id?: string;
  } | null;
  meta?: Record<string, any> | null;
}

export interface ConsentPreferenceResponse {
  notice_key: string;
  notice_history_id: string;
  value: "opt_in" | "opt_out" | "acknowledge";
  experience_config_history_id?: string | null;
  meta?: Record<string, any> | null;
}

export interface ConsentResponse {
  identity: Record<string, { value: string }>;
  preferences: ConsentPreferenceResponse[];
  scope?: Record<string, any> | null;
  meta: Record<string, any>;
}

export interface CurrentPreferencesQueryParams {
  "identity.email"?: string;
  notice_keys?: string[];
}

// V3 API Slice
export const v3Api = createApi({
  reducerPath: "v3Api",
  baseQuery: fetchBaseQuery({
    baseUrl: "/api/v3",
    prepareHeaders: (headers, { getState }) => {
      const { token } = (getState() as RootState).auth;
      addCommonHeaders(headers, token);
      return headers;
    },
  }),
  endpoints: () => ({}),
});

// V1 Endpoints (injected into the existing baseApi)
export const privacyNoticesSandboxApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getPrivacyExperience: build.query<
      Page_Union_PrivacyExperienceResponse__TCFBannerExperienceMinimalResponse__,
      PrivacyExperienceQueryParams
    >({
      query: (params) => ({
        url: "privacy-experience",
        params,
      }),
    }),
  }),
});

export const {
  useGetPrivacyExperienceQuery,
  useLazyGetPrivacyExperienceQuery,
} = privacyNoticesSandboxApi;

// V3 Endpoints (injected into the new v3Api)
export const privacyNoticesSandboxV3Api = v3Api.injectEndpoints({
  endpoints: (build) => ({
    savePrivacyPreferences: build.mutation<
      ConsentResponse,
      { body: ConsentCreate; override_children?: boolean }
    >({
      query: ({ body, override_children }) => ({
        url: "privacy-preferences",
        method: "POST",
        body,
        params: override_children ? { override_children: true } : undefined,
      }),
    }),
    getCurrentPreferences: build.query<
      ConsentPreferenceResponse[],
      CurrentPreferencesQueryParams
    >({
      query: (params) => ({
        url: `privacy-preferences/current`,
        params,
      }),
    }),
  }),
});

export const {
  useSavePrivacyPreferencesMutation,
  useLazyGetCurrentPreferencesQuery,
} = privacyNoticesSandboxV3Api;
