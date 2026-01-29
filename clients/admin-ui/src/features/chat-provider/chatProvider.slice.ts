import { baseApi } from "~/features/common/api.slice";

export interface ChatProviderSettings {
  enabled: boolean;
  provider_type: "slack";
  workspace_url?: string;
  client_id?: string;
  client_secret?: string;
  signing_secret?: string;
  notification_channel_id?: string;
}

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
  notification_channel_id?: string;
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

export interface SlackChannel {
  id: string;
  name: string;
}

export interface ChatChannelsResponse {
  channels: SlackChannel[];
}

// Conversational Q&A Feature interfaces

export interface QuestionWithAnswer {
  question: string;
  answer: string | null;
  answered_at: string | null;
  user: string | null;
  user_email: string | null;
}

export interface Conversation {
  thread_ts: string;
  channel_id: string;
  created_at: string;
  current_question_index: number;
  questions: QuestionWithAnswer[];
  status: "in_progress" | "completed";
  last_processed_ts: string;
}

export interface QuestionsResponse {
  conversations: Conversation[];
}

export interface PostQuestionsResponse {
  success: boolean;
  message: string;
  questions_posted: number;
}

// Questionnaire Feature interfaces (provider-agnostic)

export interface ChatHistoryEntry {
  timestamp: string;
  text: string;
  is_bot: boolean;
  user_email: string | null;
  user_display_name: string | null;
}

export interface QuestionResponse {
  question: string; // Canonical question (original intent)
  displayed_as: string | null; // The phrasing shown to user (may vary for freshness)
  answer: string | null;
  answered_by_email: string | null;
  answered_by_display_name: string | null;
  answered_at: string | null;
}

export interface Questionnaire {
  id: string;
  title: string;
  status: "in_progress" | "completed";
  created_at: string;
  current_question_index: number;
  questions: QuestionResponse[];
  chat_history: ChatHistoryEntry[];
}

export interface QuestionnaireListResponse {
  questionnaires: Questionnaire[];
}

export interface CreateQuestionnaireRequest {
  title: string;
  questions: string[];
}

export interface CreateQuestionnaireResponse {
  success: boolean;
  message: string;
  questionnaire_id?: string;
}

const chatProviderApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getChatSettings: build.query<ChatProviderSettingsResponse, void>({
      query: () => ({ url: "plus/chat/settings" }),
      providesTags: ["Chat Provider"],
    }),
    updateChatSettings: build.mutation<
      ChatProviderSettingsResponse,
      ChatProviderSettings
    >({
      query: (body) => ({
        url: "plus/chat/settings",
        method: "PUT",
        body,
      }),
      invalidatesTags: ["Chat Provider"],
    }),
    testChatConnection: build.mutation<ChatProviderTestResponse, void>({
      query: () => ({
        url: "plus/chat/test",
        method: "POST",
      }),
    }),
    getChatChannels: build.query<ChatChannelsResponse, void>({
      query: () => ({ url: "plus/chat/channels" }),
    }),
    deleteChatConnection: build.mutation<void, void>({
      query: () => ({
        url: "plus/chat/settings",
        method: "DELETE",
      }),
      invalidatesTags: ["Chat Provider"],
    }),
    sendChatMessage: build.mutation<SendMessageResponse, SendMessageRequest>({
      query: (body) => ({
        url: "plus/chat/send",
        method: "POST",
        body,
      }),
    }),
    // Legacy Q&A Feature endpoints
    postQuestions: build.mutation<PostQuestionsResponse, void>({
      query: () => ({
        url: "plus/chat/questions",
        method: "POST",
      }),
      invalidatesTags: ["Chat Questions"],
    }),
    getQuestions: build.query<QuestionsResponse, void>({
      query: () => ({ url: "plus/chat/questions" }),
      providesTags: ["Chat Questions"],
    }),
    // Questionnaire Feature endpoints (provider-agnostic)
    createQuestionnaire: build.mutation<
      CreateQuestionnaireResponse,
      CreateQuestionnaireRequest
    >({
      query: (body) => ({
        url: "plus/chat/questionnaire",
        method: "POST",
        body,
      }),
      invalidatesTags: ["Questionnaires"],
    }),
    getQuestionnaires: build.query<QuestionnaireListResponse, void>({
      query: () => ({ url: "plus/chat/questionnaire" }),
      providesTags: ["Questionnaires"],
    }),
    getQuestionnaire: build.query<Questionnaire, string>({
      query: (id) => ({ url: `plus/chat/questionnaire/${id}` }),
      providesTags: (_result, _error, id) => [{ type: "Questionnaires", id }],
    }),
  }),
});

export const {
  useGetChatSettingsQuery,
  useUpdateChatSettingsMutation,
  useTestChatConnectionMutation,
  useGetChatChannelsQuery,
  useDeleteChatConnectionMutation,
  useSendChatMessageMutation,
  usePostQuestionsMutation,
  useGetQuestionsQuery,
  // Questionnaire hooks
  useCreateQuestionnaireMutation,
  useGetQuestionnairesQuery,
  useGetQuestionnaireQuery,
} = chatProviderApi;
