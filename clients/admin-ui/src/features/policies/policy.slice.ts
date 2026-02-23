import { baseApi } from "~/features/common/api.slice";
import type {
  BulkPutPolicyResponse,
  MaskingStrategyDescription,
  Page_PolicyResponse_,
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

    getMaskingStrategies: build.query<MaskingStrategyDescription[], void>({
      query: () => ({ url: `/masking/strategy` }),
    }),
  }),
});

export const {
  useGetPoliciesQuery,
  useGetPolicyQuery,
  useCreateOrUpdatePoliciesMutation,
  useDeletePolicyMutation,
  useGetMaskingStrategiesQuery,
} = policyApi;
