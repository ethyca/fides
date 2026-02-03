import { baseApi } from "~/features/common/api.slice";

export interface ChatProviderSettingsResponse {
  id: string;
  enabled: boolean;
  provider_type: string;
  workspace_url?: string;
  client_id?: string;
  authorized: boolean;
  has_signing_secret: boolean;
  created_at: string;
  updated_at: string;
  workspace_name?: string;
  connected_by_email?: string;
}

export interface ChatProviderConfigCreate {
  provider_type?: "slack";
  workspace_url: string; // Required - used as unique identifier
  client_id?: string;
  client_secret?: string;
  signing_secret?: string;
}

export interface ChatProviderConfigUpdate {
  provider_type?: "slack";
  workspace_url?: string;
  client_id?: string;
  client_secret?: string;
  signing_secret?: string;
}

export interface ChatProviderSecrets {
  client_secret?: string;
  signing_secret?: string;
}

export interface ChatProviderConfigListResponse {
  items: ChatProviderSettingsResponse[];
  total: number;
}

export interface ChatProviderTestResponse {
  success: boolean;
  message: string;
}

export interface SendMessageRequest {
  channel_id: string;
  message: string;
}

export interface SendMessageResponse {
  success: boolean;
  message: string;
}

const chatProviderApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    testChatConnection: build.mutation<ChatProviderTestResponse, void>({
      query: () => ({
        url: "plus/chat/test",
        method: "POST",
      }),
    }),
    // Chat Provider Configuration CRUD endpoints
    getChatConfigs: build.query<ChatProviderConfigListResponse, void>({
      query: () => ({ url: "plus/chat/config" }),
      providesTags: ["Chat Provider Config"],
    }),
    createChatConfig: build.mutation<
      ChatProviderSettingsResponse,
      ChatProviderConfigCreate
    >({
      query: (body) => ({
        url: "plus/chat/config",
        method: "POST",
        body,
      }),
      invalidatesTags: ["Chat Provider Config"],
    }),
    getChatConfig: build.query<ChatProviderSettingsResponse, string>({
      query: (configId) => ({ url: `plus/chat/config/${configId}` }),
      providesTags: (_result, _error, id) => [{ type: "Chat Provider Config", id }],
    }),
    updateChatConfig: build.mutation<
      ChatProviderSettingsResponse,
      { configId: string; data: ChatProviderConfigUpdate }
    >({
      query: ({ configId, data }) => ({
        url: `plus/chat/config/${configId}`,
        method: "PATCH",
        body: data,
      }),
      invalidatesTags: (_result, _error, { configId }) => [
        "Chat Provider Config",
        { type: "Chat Provider Config", id: configId },
      ],
    }),
    deleteChatConfig: build.mutation<void, string>({
      query: (configId) => ({
        url: `plus/chat/config/${configId}`,
        method: "DELETE",
      }),
      invalidatesTags: ["Chat Provider Config"],
    }),
    enableChatConfig: build.mutation<ChatProviderSettingsResponse, string>({
      query: (configId) => ({
        url: `plus/chat/config/${configId}/enable`,
        method: "PUT",
      }),
      invalidatesTags: ["Chat Provider Config"],
    }),
    updateChatConfigSecrets: build.mutation<
      ChatProviderSettingsResponse,
      { configId: string; secrets: ChatProviderSecrets }
    >({
      query: ({ configId, secrets }) => ({
        url: `plus/chat/config/${configId}/secret`,
        method: "PUT",
        body: secrets,
      }),
      invalidatesTags: (_result, _error, { configId }) => [
        "Chat Provider Config",
        { type: "Chat Provider Config", id: configId },
      ],
    }),
    sendChatMessage: build.mutation<SendMessageResponse, SendMessageRequest>({
      query: (body) => ({
        url: "plus/chat/send",
        method: "POST",
        body,
      }),
    }),
  }),
});

export const {
  useTestChatConnectionMutation,
  // Chat Provider Configuration CRUD hooks
  useGetChatConfigsQuery,
  useCreateChatConfigMutation,
  useGetChatConfigQuery,
  useUpdateChatConfigMutation,
  useDeleteChatConfigMutation,
  useEnableChatConfigMutation,
  useUpdateChatConfigSecretsMutation,
  // Messaging
  useSendChatMessageMutation,
} = chatProviderApi;
