import { baseApi } from "~/features/common/api.slice";
import type { Page_PolicyResponse_, PolicyResponse } from "~/types/api";

// Policy API
const policyApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getPolicies: build.query<Page_PolicyResponse_, void>({
      query: () => ({ url: `/dsr/policy` }),
      providesTags: () => ["Policies"],
    }),

    getPolicy: build.query<PolicyResponse, string>({
      query: (policyKey) => ({ url: `/dsr/policy/${policyKey}` }),
      providesTags: (_result, _error, policyKey) => [
        { type: "Policies", id: policyKey },
      ],
    }),
  }),
});

export const { useGetPoliciesQuery, useGetPolicyQuery } = policyApi;
