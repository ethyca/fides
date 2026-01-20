/**
 * TypeScript interfaces for the AI Privacy Analyst Agent feature.
 */

// Settings
export interface AgentSettings {
  id: string;
  compliance_frameworks: string[];
  custom_system_prompt: string | null;
  organization_name: string | null;
  organization_description: string | null;
  created_at: string;
  updated_at: string;
}

export interface AgentSettingsUpdate {
  compliance_frameworks?: string[];
  custom_system_prompt?: string;
}

// Conversations
export interface Conversation {
  id: string;
  user_id: string;
  title: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ConversationCreate {
  title?: string;
}

export interface ConversationUpdate {
  title?: string;
  is_archived?: boolean;
}

export interface ConversationListResponse {
  items: Conversation[];
  total: number;
  page: number;
  size: number;
}

// Messages
export interface ToolCall {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "tool";
  content: string | null;
  tool_calls: ToolCall[] | null;
  tool_call_id: string | null;
  model_used: string | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  created_at: string;
}

export interface ConversationWithMessages extends Omit<Conversation, "message_count"> {
  messages: Message[];
}

export interface SendMessageRequest {
  content: string;
}

// SSE Events
export type SSEEventType =
  | "message_start"
  | "content_delta"
  | "tool_call"
  | "tool_result"
  | "message_end"
  | "error";

export interface SSEMessageStartEvent {
  type: "message_start";
  message_id: string;
}

export interface SSEContentDeltaEvent {
  type: "content_delta";
  content: string;
}

export interface SSEToolCallEvent {
  type: "tool_call";
  tool_call_id: string;
  tool_name: string;
  tool_arguments: Record<string, unknown>;
}

export interface SSEToolResultEvent {
  type: "tool_result";
  tool_call_id: string;
  content: string;
}

export interface SSEMessageEndEvent {
  type: "message_end";
  message_id: string;
  model_used: string | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
}

export interface SSEErrorEvent {
  type: "error";
  error: string;
  code?: string;
}

export type SSEEvent =
  | SSEMessageStartEvent
  | SSEContentDeltaEvent
  | SSEToolCallEvent
  | SSEToolResultEvent
  | SSEMessageEndEvent
  | SSEErrorEvent;

// Embeddings
export interface EmbeddingStats {
  total_embeddings: number;
  by_entity_type: Record<string, number>;
  pending_queue_items: number;
  oldest_updated_at: string | null;
  newest_updated_at: string | null;
}

export interface EmbeddingSyncRequest {
  entity_types?: string[];
}

export interface EmbeddingSyncResponse {
  status: string;
  message: string;
  entity_types: string[];
}

// Streaming state
export interface StreamingState {
  isStreaming: boolean;
  messageId: string | null;
  content: string;
  toolCalls: ToolCall[];
  toolResults: Map<string, string>;
  error: string | null;
}
