import { baseApi } from "~/features/common/api.slice";
import type { Page_Union_PrivacyExperienceResponse__TCFBannerExperienceMinimalResponse__ } from "~/types/api";

// Get the V3 API base URL from environment variables
// Falls back to localhost for development if not set
const V3_API_BASE_URL =
  process.env.NEXT_PUBLIC_FIDESCTL_API_SERVER || "http://localhost:8080";

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
    savePrivacyPreferences: build.mutation<
      ConsentResponse,
      { body: ConsentCreate; override_children?: boolean }
    >({
      query: ({ body, override_children }) => ({
        url: `${V3_API_BASE_URL}/api/v3/privacy-preferences`,
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
        url: `${V3_API_BASE_URL}/api/v3/privacy-preferences/current`,
        params,
      }),
    }),
  }),
});

export const {
  useGetPrivacyExperienceQuery,
  useLazyGetPrivacyExperienceQuery,
  useSavePrivacyPreferencesMutation,
  useLazyGetCurrentPreferencesQuery,
} = privacyNoticesSandboxApi;
