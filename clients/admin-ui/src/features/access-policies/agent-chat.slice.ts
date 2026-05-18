import { baseApi } from "~/features/common/api.slice";

export interface AccessPolicyChatRequest {
  prompt: string;
  chat_history_id?: string;
  current_policy_yaml?: string;
}

/**
 * Bundles a proposed policy change from the agent. The id buckets drive the
 * visual editor's animation:
 *   - added/changed → highlight pulses on the new graph
 *   - removed → ghost nodes during the hold phase
 *
 * Id format (matches the system prompt taught to the LLM):
 *   - "policy"
 *   - "action"
 *   - "condition:<dimension>"               e.g. "condition:data_use"
 *   - "constraint:<type>:<discriminator>"   e.g. "constraint:geo_location:..."
 */
export interface PolicyUpdate {
  yaml: string;
  added: string[];
  changed: string[];
  removed: string[];
}

export interface AccessPolicyChatResponse {
  chat_history_id: string;
  message: string;
  policy_update: PolicyUpdate | null;
}

const agentChatApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    sendAccessPolicyChatMessage: build.mutation<
      AccessPolicyChatResponse,
      AccessPolicyChatRequest
    >({
      query: (body) => ({
        method: "POST",
        url: "plus/access-policy/agent",
        body,
      }),
    }),
  }),
});

export const { useSendAccessPolicyChatMessageMutation } = agentChatApi;
