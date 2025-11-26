import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import { addCommonHeaders } from "~/features/common/CommonHeaders";
import type { Page_Union_PrivacyExperienceResponse__TCFBannerExperienceMinimalResponse__ } from "~/types/api";
import type { ConsentCreate } from "~/types/api/models/ConsentCreate";
import type { ConsentPreferenceResponse } from "~/types/api/models/ConsentPreferenceResponse";
import type { ConsentResponse } from "~/types/api/models/ConsentResponse";
import type { PropagationPolicyKey } from "~/types/api/models/PropagationPolicyKey";

export interface PrivacyExperienceQueryParams {
  region: string;
  show_disabled: boolean;
  property_id?: string;
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
      { body: ConsentCreate; policy?: PropagationPolicyKey | null }
    >({
      query: ({ body, policy }) => ({
        url: "privacy-preferences",
        method: "POST",
        body,
        params: policy ? { policy } : undefined,
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
