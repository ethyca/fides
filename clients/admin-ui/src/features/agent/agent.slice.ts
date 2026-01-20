/**
 * RTK Query slice for the AI Privacy Analyst Agent.
 */

import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { baseApi } from "~/features/common/api.slice";

import type {
  AgentSettings,
  AgentSettingsUpdate,
  Conversation,
  ConversationCreate,
  ConversationListResponse,
  ConversationUpdate,
  ConversationWithMessages,
  EmbeddingStats,
  EmbeddingSyncRequest,
  EmbeddingSyncResponse,
} from "./types";

// API slice
const agentApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    // Settings endpoints
    getAgentSettings: build.query<AgentSettings, void>({
      query: () => ({ url: "plus/agent/settings" }),
      providesTags: ["Agent Settings"],
    }),

    updateAgentSettings: build.mutation<AgentSettings, AgentSettingsUpdate>({
      query: (body) => ({
        url: "plus/agent/settings",
        method: "PUT",
        body,
      }),
      invalidatesTags: ["Agent Settings"],
    }),

    // Conversation endpoints
    listConversations: build.query<
      ConversationListResponse,
      { page?: number; size?: number; include_archived?: boolean }
    >({
      query: ({ page = 1, size = 20, include_archived = false }) => ({
        url: `plus/agent/conversations`,
        params: { page, size, include_archived },
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.items.map(({ id }) => ({
                type: "Agent Conversations" as const,
                id,
              })),
              { type: "Agent Conversations", id: "LIST" },
            ]
          : [{ type: "Agent Conversations", id: "LIST" }],
    }),

    getConversation: build.query<ConversationWithMessages, string>({
      query: (id) => ({ url: `plus/agent/conversations/${id}` }),
      providesTags: (result, error, id) => [
        { type: "Agent Conversations", id },
      ],
    }),

    createConversation: build.mutation<Conversation, ConversationCreate>({
      query: (body) => ({
        url: "plus/agent/conversations",
        method: "POST",
        body,
      }),
      invalidatesTags: [{ type: "Agent Conversations", id: "LIST" }],
    }),

    updateConversation: build.mutation<
      Conversation,
      { id: string; data: ConversationUpdate }
    >({
      query: ({ id, data }) => ({
        url: `plus/agent/conversations/${id}`,
        method: "PATCH",
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: "Agent Conversations", id },
        { type: "Agent Conversations", id: "LIST" },
      ],
    }),

    deleteConversation: build.mutation<void, string>({
      query: (id) => ({
        url: `plus/agent/conversations/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: [{ type: "Agent Conversations", id: "LIST" }],
    }),

    // Embedding endpoints
    getEmbeddingStatus: build.query<EmbeddingStats, void>({
      query: () => ({ url: "plus/agent/embeddings/status" }),
      providesTags: ["Agent Embeddings"],
    }),

    syncEmbeddings: build.mutation<EmbeddingSyncResponse, EmbeddingSyncRequest | void>({
      query: (body) => ({
        url: "plus/agent/embeddings/sync",
        method: "POST",
        body: body || {},
      }),
      invalidatesTags: ["Agent Embeddings"],
    }),
  }),
});

export const {
  // Settings
  useGetAgentSettingsQuery,
  useUpdateAgentSettingsMutation,
  // Conversations
  useListConversationsQuery,
  useGetConversationQuery,
  useCreateConversationMutation,
  useUpdateConversationMutation,
  useDeleteConversationMutation,
  // Embeddings
  useGetEmbeddingStatusQuery,
  useSyncEmbeddingsMutation,
} = agentApi;

// Local state slice for streaming
interface AgentState {
  currentConversationId: string | null;
  isStreaming: boolean;
  streamingContent: string;
  streamingToolCalls: Array<{
    id: string;
    name: string;
    arguments: Record<string, unknown>;
    result?: string;
  }>;
  streamingError: string | null;
}

const initialState: AgentState = {
  currentConversationId: null,
  isStreaming: false,
  streamingContent: "",
  streamingToolCalls: [],
  streamingError: null,
};

export const agentSlice = createSlice({
  name: "agent",
  initialState,
  reducers: {
    setCurrentConversation: (state, action: PayloadAction<string | null>) => {
      state.currentConversationId = action.payload;
    },
    startStreaming: (state) => {
      state.isStreaming = true;
      state.streamingContent = "";
      state.streamingToolCalls = [];
      state.streamingError = null;
    },
    appendStreamContent: (state, action: PayloadAction<string>) => {
      state.streamingContent += action.payload;
    },
    addToolCall: (
      state,
      action: PayloadAction<{
        id: string;
        name: string;
        arguments: Record<string, unknown>;
      }>
    ) => {
      state.streamingToolCalls.push(action.payload);
    },
    setToolResult: (
      state,
      action: PayloadAction<{ toolCallId: string; result: string }>
    ) => {
      const toolCall = state.streamingToolCalls.find(
        (tc) => tc.id === action.payload.toolCallId
      );
      if (toolCall) {
        toolCall.result = action.payload.result;
      }
    },
    stopStreaming: (state) => {
      state.isStreaming = false;
    },
    setStreamingError: (state, action: PayloadAction<string>) => {
      state.streamingError = action.payload;
      state.isStreaming = false;
    },
    resetStreamingState: (state) => {
      state.isStreaming = false;
      state.streamingContent = "";
      state.streamingToolCalls = [];
      state.streamingError = null;
    },
  },
});

export const {
  setCurrentConversation,
  startStreaming,
  appendStreamContent,
  addToolCall,
  setToolResult,
  stopStreaming,
  setStreamingError,
  resetStreamingState,
} = agentSlice.actions;

export const { reducer } = agentSlice;

// Selectors
export const selectCurrentConversationId = (state: {
  agent: AgentState;
}): string | null => state.agent.currentConversationId;
export const selectIsStreaming = (state: { agent: AgentState }): boolean =>
  state.agent.isStreaming;
export const selectStreamingContent = (state: { agent: AgentState }): string =>
  state.agent.streamingContent;
export const selectStreamingToolCalls = (state: {
  agent: AgentState;
}): AgentState["streamingToolCalls"] => state.agent.streamingToolCalls;
export const selectStreamingError = (state: {
  agent: AgentState;
}): string | null => state.agent.streamingError;
