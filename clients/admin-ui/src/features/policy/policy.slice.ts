import { baseApi } from "~/features/common/api.slice";
import {
  Page_PolicyResponse_,
  Page_RuleResponseWithTargets_,
  RuleResponseWithTargets,
} from "~/types/api";

// Policy API
const policyApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getPolicies: build.query<Page_PolicyResponse_, void>({
      query: () => ({ url: `/dsr/policy` }),
      providesTags: () => ["Policies"],
    }),

    // Fetch rule details for a specific policy and rule
    getRuleWithTargets: build.query<
      RuleResponseWithTargets,
      { policyKey: string; ruleKey: string }
    >({
      query: ({ policyKey, ruleKey }) => ({
        url: `/dsr/policy/${policyKey}/rule/${ruleKey}`,
      }),
      providesTags: () => ["Policies"],
    }),

    // Fetch all rules for a policy with their targets
    getPolicyRules: build.query<
      Page_RuleResponseWithTargets_,
      { policyKey: string }
    >({
      query: ({ policyKey }) => ({
        url: `/dsr/policy/${policyKey}/rule`,
      }),
      providesTags: () => ["Policies"],
    }),
  }),
});

export const {
  useGetPoliciesQuery,
  useGetRuleWithTargetsQuery,
  useGetPolicyRulesQuery,
} = policyApi;
