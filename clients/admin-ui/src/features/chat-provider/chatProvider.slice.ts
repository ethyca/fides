import { baseApi } from "~/features/common/api.slice";
import type {
  ChatChannelsResponse,
  ChatConfigCreate,
  ChatConfigListResponse,
  ChatConfigResponse,
  ChatConfigSecrets,
  ChatConfigTestResponse,
  ChatConfigUpdate,
  SendMessageRequest,
  SendMessageResponse,
} from "~/types/api";

const chatProviderApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    testChatConnection: build.mutation<ChatConfigTestResponse, void>({
      query: () => ({
        url: "plus/chat/test",
        method: "POST",
      }),
    }),
    // Chat Provider Configuration CRUD endpoints
    getChatConfigs: build.query<ChatConfigListResponse, void>({
      query: () => ({ url: "plus/chat/config" }),
      providesTags: ["Chat Provider Config"],
    }),
    createChatConfig: build.mutation<ChatConfigResponse, ChatConfigCreate>({
      query: (body) => ({
        url: "plus/chat/config",
        method: "POST",
        body,
      }),
      invalidatesTags: ["Chat Provider Config"],
    }),
    getChatConfig: build.query<ChatConfigResponse, string>({
      query: (configId) => ({ url: `plus/chat/config/${configId}` }),
      providesTags: (_result, _error, id) => [
        { type: "Chat Provider Config", id },
      ],
    }),
    updateChatConfig: build.mutation<
      ChatConfigResponse,
      { configId: string; data: ChatConfigUpdate }
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
    enableChatConfig: build.mutation<ChatConfigResponse, string>({
      query: (configId) => ({
        url: `plus/chat/config/${configId}/enable`,
        method: "PUT",
      }),
      invalidatesTags: ["Chat Provider Config"],
    }),
    updateChatConfigSecrets: build.mutation<
      ChatConfigResponse,
      { configId: string; secrets: ChatConfigSecrets }
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
    getChatChannels: build.query<ChatChannelsResponse, void>({
      query: () => ({
        url: "plus/chat/channels",
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
  // Channels
  useGetChatChannelsQuery,
} = chatProviderApi;
