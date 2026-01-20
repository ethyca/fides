import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import {
  EvaluateContext,
  EvaluateResponse,
  PolicyV2,
  PolicyV2Create,
  PolicyV2ListResponse,
  PolicyV2Update,
} from "./types";

export interface State {
  activePolicyId?: string;
}

const initialState: State = {};

interface PolicyV2Params {
  enabled_only?: boolean;
}

interface EvaluateRequest {
  policy_key?: string;
  context?: EvaluateContext;
}

interface PolicyV2ChatRequest {
  message: string;
  session_id?: string | null;
  model?: string;
}

interface PolicyV2ChatResponse {
  session_id: string;
  assistant_message: string;
  generated_policy?: PolicyV2Create | null;
  is_policy_complete: boolean;
}

type PolicyV2UpdateParams = PolicyV2Update & { fides_key: string };

const policyV2Api = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllPoliciesV2: build.query<PolicyV2ListResponse, PolicyV2Params>({
      query: (params) => ({
        url: `policies-v2`,
        params,
      }),
      providesTags: () => ["Policies V2"],
    }),
    getPolicyV2ByKey: build.query<PolicyV2, string>({
      query: (fidesKey) => ({
        url: `policies-v2/${fidesKey}`,
      }),
      providesTags: (result, error, arg) => [{ type: "Policies V2", id: arg }],
    }),
    createPolicyV2: build.mutation<PolicyV2, PolicyV2Create>({
      query: (payload) => ({
        method: "POST",
        url: `policies-v2`,
        body: payload,
      }),
      invalidatesTags: () => ["Policies V2"],
    }),
    updatePolicyV2: build.mutation<PolicyV2, PolicyV2UpdateParams>({
      query: (payload) => {
        const { fides_key, ...body } = payload;
        return {
          method: "PUT",
          url: `policies-v2/${fides_key}`,
          body,
        };
      },
      invalidatesTags: (result, error, arg) => [
        "Policies V2",
        { type: "Policies V2", id: arg.fides_key },
      ],
    }),
    deletePolicyV2: build.mutation<void, string>({
      query: (fidesKey) => ({
        method: "DELETE",
        url: `policies-v2/${fidesKey}`,
      }),
      invalidatesTags: () => ["Policies V2"],
    }),
    evaluatePolicy: build.mutation<EvaluateResponse, EvaluateRequest>({
      query: (payload) => ({
        method: "POST",
        url: `evaluate`,
        body: payload,
      }),
    }),
    sendPolicyV2Chat: build.mutation<PolicyV2ChatResponse, PolicyV2ChatRequest>({
      query: (payload) => ({
        method: "POST",
        url: `policy-v2/chat`,
        body: payload,
      }),
    }),
    clearPolicyV2Chat: build.mutation<{ status: string }, string>({
      query: (sessionId) => ({
        method: "DELETE",
        url: `policy-v2/chat/${sessionId}`,
      }),
    }),
  }),
});

export const {
  useGetAllPoliciesV2Query,
  useGetPolicyV2ByKeyQuery,
  useLazyGetPolicyV2ByKeyQuery,
  useCreatePolicyV2Mutation,
  useUpdatePolicyV2Mutation,
  useDeletePolicyV2Mutation,
  useEvaluatePolicyMutation,
  useSendPolicyV2ChatMutation,
  useClearPolicyV2ChatMutation,
} = policyV2Api;

export const policyV2Slice = createSlice({
  name: "policyV2",
  initialState,
  reducers: {
    setActivePolicyId: (
      draftState,
      action: PayloadAction<string | undefined>,
    ) => {
      draftState.activePolicyId = action.payload;
    },
  },
});

export const { setActivePolicyId } = policyV2Slice.actions;

export const { reducer } = policyV2Slice;

const selectPolicyV2 = (state: RootState) => state.policyV2;

export const selectActivePolicyId = createSelector(
  selectPolicyV2,
  (state) => state.activePolicyId,
);

const emptyPolicies: PolicyV2[] = [];
export const selectAllPoliciesV2 = createSelector(
  [(RootState) => RootState],
  (RootState) => {
    const data: PolicyV2ListResponse | undefined =
      policyV2Api.endpoints.getAllPoliciesV2.select({})(RootState)?.data;
    return data ? data.items : emptyPolicies;
  },
);
