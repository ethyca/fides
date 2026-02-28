import { baseApi } from "~/features/common/api.slice";
import type {
  BulkPutPolicyResponse,
  MaskingStrategyDescription,
  Page_PolicyResponse_,
  PolicyConditionRequest,
  PolicyConditionResponse,
  PolicyResponse,
} from "~/types/api";

interface PolicyCreateUpdate {
  name: string;
  key?: string;
  execution_timeframe?: number | null;
}

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

    createOrUpdatePolicies: build.mutation<
      BulkPutPolicyResponse,
      PolicyCreateUpdate[]
    >({
      query: (policies) => ({
        url: `/dsr/policy`,
        method: "PATCH",
        body: policies,
      }),
      invalidatesTags: ["Policies"],
    }),

    deletePolicy: build.mutation<void, string>({
      query: (policyKey) => ({
        url: `/dsr/policy/${policyKey}`,
        method: "DELETE",
      }),
      invalidatesTags: ["Policies"],
    }),

    getDefaultPolicies: build.query<Record<string, string>, void>({
      query: () => ({ url: `/plus/dsr/policy/default` }),
      providesTags: ["Policies"],
    }),

    getMaskingStrategies: build.query<MaskingStrategyDescription[], void>({
      query: () => ({ url: `/masking/strategy` }),
    }),

    updatePolicyConditions: build.mutation<
      PolicyConditionResponse,
      { policyKey: string; condition: PolicyConditionRequest["condition"] }
    >({
      query: ({ policyKey, condition }) => ({
        url: `/plus/dsr/policy/${policyKey}/conditions`,
        method: "PUT",
        body: { condition },
      }),
      invalidatesTags: (_r, _e, { policyKey }) => [
        { type: "Policies", id: policyKey },
        "Policies",
      ],
    }),
  }),
});

export const {
  useGetPoliciesQuery,
  useGetPolicyQuery,
  useGetDefaultPoliciesQuery,
  useCreateOrUpdatePoliciesMutation,
  useDeletePolicyMutation,
  useGetMaskingStrategiesQuery,
  useUpdatePolicyConditionsMutation,
} = policyApi;
