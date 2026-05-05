import { baseApi } from "~/features/common/api.slice";

export interface AccessPolicyChatRequest {
  prompt: string;
  chat_history_id?: string;
  current_policy_yaml?: string;
}

export interface AccessPolicyChatResponse {
  chat_history_id: string;
  message: string;
  new_policy_yaml: string | null;
}

const agentChatApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    sendAccessPolicyChatMessage: build.mutation<
      AccessPolicyChatResponse,
      AccessPolicyChatRequest
    >({
      query: (body) => ({
        method: "POST",
        url: "plus/llm/access-policy-chat",
        body,
      }),
    }),
  }),
});

export const { useSendAccessPolicyChatMessageMutation } = agentChatApi;
