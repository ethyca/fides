import { baseApi } from "~/features/common/api.slice";

import type {
  GeneratePoliciesResponse,
  OnboardingConfigResponse,
  OnboardingDataUsesResponse,
  OnboardingIndustriesResponse,
} from "./types";

export interface Control {
  key: string;
  label: string;
}

export interface AccessPolicy {
  id: string;
  name: string;
  description?: string;
  controls?: string[];
  yaml?: string;
  is_recommendation?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface AccessPolicyListResponse {
  items: AccessPolicy[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

const accessPoliciesApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAccessPolicies: build.query<
      AccessPolicyListResponse,
      { page?: number; size?: number }
    >({
      query: ({ page = 1, size = 50 } = {}) => ({
        method: "GET",
        url: "plus/access-policy",
        params: { page, size },
      }),
      providesTags: () => ["Access Policies"],
    }),
    getAccessPolicy: build.query<AccessPolicy, string>({
      query: (id) => ({
        method: "GET",
        url: `plus/access-policy/${id}`,
      }),
      providesTags: (_result, _error, id) => [{ type: "Access Policies", id }],
    }),
    createAccessPolicy: build.mutation<AccessPolicy, Partial<AccessPolicy>>({
      query: (body) => ({
        method: "POST",
        url: "plus/access-policy",
        body,
      }),
      invalidatesTags: ["Access Policies"],
    }),
    updateAccessPolicy: build.mutation<
      AccessPolicy,
      { id: string } & Partial<AccessPolicy>
    >({
      query: ({ id, ...body }) => ({
        method: "PATCH",
        url: `plus/access-policy/${id}`,
        body,
      }),
      invalidatesTags: (_result, _error, { id }) => [
        "Access Policies",
        { type: "Access Policies", id },
      ],
    }),
    deleteAccessPolicy: build.mutation<void, string>({
      query: (id) => ({
        method: "DELETE",
        url: `plus/access-policy/${id}`,
      }),
      invalidatesTags: ["Access Policies"],
    }),
    reorderAccessPolicy: build.mutation<
      void,
      { id: string; insert_after_id: string | null }
    >({
      query: ({ id, insert_after_id }) => ({
        method: "POST",
        url: `plus/access-policy/${id}/reorder`,
        body: { insert_after_id },
      }),
      invalidatesTags: ["Access Policies"],
    }),
    getControls: build.query<Control[], void>({
      query: () => ({
        method: "GET",
        url: "plus/controls",
      }),
      providesTags: ["Controls"],
    }),
    createControl: build.mutation<Control, { key: string; label: string }>({
      query: (body) => ({
        method: "POST",
        url: "plus/controls",
        body,
      }),
      invalidatesTags: ["Controls"],
    }),
    updateControl: build.mutation<Control, { key: string; label: string }>({
      query: ({ key, ...body }) => ({
        method: "PATCH",
        url: `plus/controls/${key}`,
        body,
      }),
      invalidatesTags: ["Controls"],
    }),
    deleteControl: build.mutation<void, string>({
      query: (key) => ({
        method: "DELETE",
        url: `plus/controls/${key}`,
      }),
      invalidatesTags: ["Controls", "Access Policies"],
    }),
    getOnboardingIndustries: build.query<OnboardingIndustriesResponse, void>({
      query: () => ({
        method: "GET",
        url: "plus/access-policy/presets/industries",
      }),
    }),
    getOnboardingDataUses: build.query<
      OnboardingDataUsesResponse,
      { industry: string; geographies: string[] }
    >({
      query: ({ industry, geographies }) => {
        const params = new URLSearchParams();
        params.append("industry", industry);
        geographies.forEach((g) => params.append("geographies", g));
        return {
          method: "GET",
          url: `plus/access-policy/presets/data-uses?${params.toString()}`,
        };
      },
    }),
    getOnboardingConfig: build.query<OnboardingConfigResponse, void>({
      query: () => ({
        method: "GET",
        url: "plus/access-policy/presets/config",
      }),
    }),
    generatePolicies: build.mutation<GeneratePoliciesResponse, FormData>({
      query: (formData) => ({
        method: "POST",
        url: "plus/access-policy/presets/generate",
        body: formData,
      }),
      invalidatesTags: ["Access Policies"],
    }),
  }),
});

export const {
  useGetAccessPoliciesQuery,
  useGetAccessPolicyQuery,
  useCreateAccessPolicyMutation,
  useUpdateAccessPolicyMutation,
  useDeleteAccessPolicyMutation,
  useReorderAccessPolicyMutation,
  useGetControlsQuery,
  useCreateControlMutation,
  useUpdateControlMutation,
  useDeleteControlMutation,
  useGetOnboardingIndustriesQuery,
  useGetOnboardingDataUsesQuery,
  useGetOnboardingConfigQuery,
  useGeneratePoliciesMutation,
} = accessPoliciesApi;
