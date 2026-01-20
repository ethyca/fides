/**
 * Agent feature barrel export.
 */

// Components
export { default as AgentChat } from "./AgentChat";
export { default as AgentChatInput } from "./AgentChatInput";
export { default as AgentChatMessage } from "./AgentChatMessage";
export { default as AgentConversationList } from "./AgentConversationList";
export { default as AgentWelcome } from "./AgentWelcome";

// Hooks
export { useStreamingMessage } from "./hooks";

// RTK Query hooks and actions
export {
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
  // Actions
  setCurrentConversation,
  startStreaming,
  appendStreamContent,
  addToolCall,
  setToolResult,
  stopStreaming,
  setStreamingError,
  resetStreamingState,
  // Selectors
  selectCurrentConversationId,
  selectIsStreaming,
  selectStreamingContent,
  selectStreamingToolCalls,
  selectStreamingError,
  // Reducer
  reducer as agentReducer,
} from "./agent.slice";

// Types
export type {
  AgentSettings,
  AgentSettingsUpdate,
  Conversation,
  ConversationCreate,
  ConversationUpdate,
  ConversationListResponse,
  ConversationWithMessages,
  Message,
  ToolCall,
  SSEEvent,
  StreamingState,
  EmbeddingStats,
  EmbeddingSyncRequest,
  EmbeddingSyncResponse,
} from "./types";
