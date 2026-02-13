import { baseApi } from "~/features/common/api.slice";
import type {
  BulkPutPolicyResponse,
  BulkPutRuleResponse,
  BulkPutRuleTargetResponse,
  ConditionGroup,
  Page_PolicyResponse_,
  Page_RuleResponseWithTargets_,
  PolicyResponse,
  RuleTarget,
} from "~/types/api";

// Policy request/response types
interface PolicyCreateUpdate {
  name: string;
  key?: string;
  drp_action?: string | null;
  execution_timeframe?: number | null;
}

interface RuleCreateUpdate {
  name: string;
  key?: string;
  action_type: string;
  storage_destination_key?: string | null;
  masking_strategy?: {
    strategy: string;
    configuration?: Record<string, unknown>;
  } | null;
}

interface RuleTargetCreateUpdate {
  name?: string;
  key?: string;
  data_category: string;
}

interface PolicyConditionsUpdate {
  conditions: ConditionGroup[];
}

// Policy API
const policyApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    // === Policies ===
    getPolicies: build.query<
      Page_PolicyResponse_,
      { page?: number; size?: number } | void
    >({
      query: (params) => ({
        url: `/dsr/policy`,
        params: params ?? { size: 100 },
      }),
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

    // === Rules ===
    getPolicyRules: build.query<Page_RuleResponseWithTargets_, string>({
      query: (policyKey) => ({ url: `/dsr/policy/${policyKey}/rule` }),
      providesTags: (_result, _error, policyKey) => [
        { type: "Policies", id: `${policyKey}-rules` },
      ],
    }),

    createOrUpdateRules: build.mutation<
      BulkPutRuleResponse,
      { policyKey: string; rules: RuleCreateUpdate[] }
    >({
      query: ({ policyKey, rules }) => ({
        url: `/dsr/policy/${policyKey}/rule`,
        method: "PATCH",
        body: rules,
      }),
      invalidatesTags: (_result, _error, { policyKey }) => [
        { type: "Policies", id: policyKey },
        { type: "Policies", id: `${policyKey}-rules` },
      ],
    }),

    deleteRule: build.mutation<void, { policyKey: string; ruleKey: string }>({
      query: ({ policyKey, ruleKey }) => ({
        url: `/dsr/policy/${policyKey}/rule/${ruleKey}`,
        method: "DELETE",
      }),
      invalidatesTags: (_result, _error, { policyKey }) => [
        { type: "Policies", id: policyKey },
        { type: "Policies", id: `${policyKey}-rules` },
      ],
    }),

    // === Rule Targets ===
    getRuleTargets: build.query<
      RuleTarget[],
      { policyKey: string; ruleKey: string }
    >({
      query: ({ policyKey, ruleKey }) => ({
        url: `/dsr/policy/${policyKey}/rule/${ruleKey}/target`,
      }),
      providesTags: (_result, _error, { policyKey, ruleKey }) => [
        { type: "Policies", id: `${policyKey}-${ruleKey}-targets` },
      ],
    }),

    createOrUpdateTargets: build.mutation<
      BulkPutRuleTargetResponse,
      { policyKey: string; ruleKey: string; targets: RuleTargetCreateUpdate[] }
    >({
      query: ({ policyKey, ruleKey, targets }) => ({
        url: `/dsr/policy/${policyKey}/rule/${ruleKey}/target`,
        method: "PATCH",
        body: targets,
      }),
      invalidatesTags: (_result, _error, { policyKey, ruleKey }) => [
        { type: "Policies", id: policyKey },
        { type: "Policies", id: `${policyKey}-rules` },
        { type: "Policies", id: `${policyKey}-${ruleKey}-targets` },
      ],
    }),

    deleteTarget: build.mutation<
      void,
      { policyKey: string; ruleKey: string; targetKey: string }
    >({
      query: ({ policyKey, ruleKey, targetKey }) => ({
        url: `/dsr/policy/${policyKey}/rule/${ruleKey}/target/${targetKey}`,
        method: "DELETE",
      }),
      invalidatesTags: (_result, _error, { policyKey, ruleKey }) => [
        { type: "Policies", id: policyKey },
        { type: "Policies", id: `${policyKey}-rules` },
        { type: "Policies", id: `${policyKey}-${ruleKey}-targets` },
      ],
    }),

    // === Policy Conditions ===
    updatePolicyConditions: build.mutation<
      void,
      { policyKey: string; conditions: PolicyConditionsUpdate }
    >({
      query: ({ policyKey, conditions }) => ({
        url: `/dsr/policy/${policyKey}/conditions`,
        method: "PUT",
        body: conditions,
      }),
      invalidatesTags: (_result, _error, { policyKey }) => [
        { type: "Policies", id: policyKey },
      ],
    }),
  }),
});

export const {
  useGetPoliciesQuery,
  useGetPolicyQuery,
  useCreateOrUpdatePoliciesMutation,
  useDeletePolicyMutation,
  useGetPolicyRulesQuery,
  useCreateOrUpdateRulesMutation,
  useDeleteRuleMutation,
  useGetRuleTargetsQuery,
  useCreateOrUpdateTargetsMutation,
  useDeleteTargetMutation,
  useUpdatePolicyConditionsMutation,
} = policyApi;
