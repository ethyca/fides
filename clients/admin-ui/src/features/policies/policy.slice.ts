import { baseApi } from "~/features/common/api.slice";
import type {
  MaskingStrategyDescription,
  Page_PolicyResponse_,
  PolicyResponse,
} from "~/types/api";

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

    getMaskingStrategies: build.query<MaskingStrategyDescription[], void>({
      query: () => ({ url: `/masking/strategy` }),
    }),
  }),
});

export const {
  useGetPoliciesQuery,
  useGetPolicyQuery,
  useGetMaskingStrategiesQuery,
} = policyApi;
