import { saveAs } from "file-saver";

import { baseApi } from "~/features/common/api.slice";
import type {
  CreateAssessmentTaskRequest,
  Page_TemplateResponse_,
} from "~/types/api";

import {
  AssessmentEvidenceResponse,
  AssessmentStatus,
  AssessmentTaskPage,
  AssessmentTaskResponse,
  BulkUpdateAnswersRequest,
  BulkUpdateAnswersResponse,
  ChatReplyRequest,
  ChatReplyResponse,
  CreateAssessmentTaskResponse,
  CreateQuestionnaireRequest,
  CreateReminderRequest,
  GetAssessmentEvidenceParams,
  GroupedAssessmentsResponse,
  PrivacyAssessmentConfigDefaults,
  PrivacyAssessmentConfigResponse,
  PrivacyAssessmentConfigUpdate,
  PrivacyAssessmentDetailResponse,
  PrivacyAssessmentResponse,
  QuestionnaireChatMessage,
  QuestionnaireResponse,
  QuestionnaireSessionStatus,
  QuestionnaireStatusResponse,
  ReminderResponse,
  StartChatRequest,
  StartChatResponse,
  UpdateAnswerRequest,
  UpdateAnswerResponse,
  UpdatePrivacyAssessmentRequest,
} from "./types";

const privacyAssessmentsApi = baseApi.injectEndpoints({
  overrideExisting: true,
  endpoints: (build) => ({
    getPrivacyAssessments: build.query<
      GroupedAssessmentsResponse,
      { page?: number; size?: number; status?: AssessmentStatus } | void
    >({
      query: (params) => ({
        url: "plus/privacy-assessments",
        params: params ?? undefined,
      }),
      providesTags: ["Privacy Assessment"],
    }),

    getAssessmentTemplates: build.query<
      Page_TemplateResponse_,
      { page?: number; size?: number } | void
    >({
      query: (params) => ({
        url: "plus/privacy-assessments/templates",
        params: params ?? undefined,
      }),
    }),

    getPrivacyAssessment: build.query<PrivacyAssessmentDetailResponse, string>({
      query: (id) => ({
        url: `plus/privacy-assessments/${id}`,
      }),
      providesTags: (_result, _error, id) => [
        { type: "Privacy Assessment", id },
      ],
    }),

    createPrivacyAssessment: build.mutation<
      CreateAssessmentTaskResponse,
      CreateAssessmentTaskRequest
    >({
      query: (body) => ({
        url: "plus/privacy-assessments",
        method: "POST",
        body: { high_risk_only: false, ...body }, // Temporary fix to ensure all assessments are generated
      }),
      invalidatesTags: ["Privacy Assessment", "Privacy Assessment Tasks"],
    }),

    getAssessmentTasks: build.query<
      AssessmentTaskPage,
      { page?: number; size?: number; status?: string } | void
    >({
      query: (params) => ({
        url: "plus/privacy-assessments/tasks",
        params: params ?? undefined,
      }),
      providesTags: ["Privacy Assessment Tasks"],
    }),

    getAssessmentTask: build.query<AssessmentTaskResponse, string>({
      query: (taskId) => ({
        url: `plus/privacy-assessments/tasks/${taskId}`,
      }),
      providesTags: (_result, _error, taskId) => [
        { type: "Privacy Assessment Tasks", id: taskId },
      ],
    }),

    updatePrivacyAssessment: build.mutation<
      PrivacyAssessmentResponse,
      { id: string; body: UpdatePrivacyAssessmentRequest }
    >({
      query: ({ id, body }) => ({
        url: `plus/privacy-assessments/${id}`,
        method: "PUT",
        body,
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: "Privacy Assessment", id },
        "Privacy Assessment",
      ],
    }),

    deletePrivacyAssessment: build.mutation<void, string>({
      query: (id) => ({
        url: `plus/privacy-assessments/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: ["Privacy Assessment"],
    }),

    updateAssessmentAnswer: build.mutation<
      UpdateAnswerResponse,
      { id: string; questionId: string; body: UpdateAnswerRequest }
    >({
      query: ({ id, questionId, body }) => ({
        url: `plus/privacy-assessments/${id}/questions/${questionId}`,
        method: "PUT",
        body,
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: "Privacy Assessment", id },
        "Privacy Assessment",
        { type: "Privacy Assessment Evidence", id },
      ],
    }),

    bulkUpdateAssessmentAnswers: build.mutation<
      BulkUpdateAnswersResponse,
      { id: string; body: BulkUpdateAnswersRequest }
    >({
      query: ({ id, body }) => ({
        url: `plus/privacy-assessments/${id}/questions`,
        method: "PUT",
        body,
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: "Privacy Assessment", id },
        "Privacy Assessment",
        { type: "Privacy Assessment Evidence", id },
      ],
    }),

    getAssessmentEvidence: build.query<
      AssessmentEvidenceResponse,
      GetAssessmentEvidenceParams
    >({
      query: ({ id, ...params }) => ({
        url: `plus/privacy-assessments/${id}/evidence`,
        params,
      }),
      providesTags: (_result, _error, { id }) => [
        { type: "Privacy Assessment Evidence", id },
      ],
    }),

    createQuestionnaire: build.mutation<
      QuestionnaireResponse,
      { id: string; body: CreateQuestionnaireRequest }
    >({
      query: ({ id, body }) => ({
        url: `plus/privacy-assessments/${id}/questionnaire`,
        method: "POST",
        body,
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: "Privacy Assessment Questionnaire", id },
        { type: "Privacy Assessment", id },
      ],
    }),

    getQuestionnaireStatus: build.query<QuestionnaireStatusResponse, string>({
      query: (id) => ({
        url: `plus/privacy-assessments/${id}/questionnaire`,
      }),
      providesTags: (_result, _error, id) => [
        { type: "Privacy Assessment Questionnaire", id },
      ],
    }),

    createQuestionnaireReminder: build.mutation<
      ReminderResponse,
      { id: string; body?: CreateReminderRequest }
    >({
      query: ({ id, body }) => ({
        url: `plus/privacy-assessments/${id}/questionnaire/reminders`,
        method: "POST",
        body: body ?? {},
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: "Privacy Assessment Questionnaire", id },
      ],
    }),

    // Assessment Configuration Endpoints
    getAssessmentConfig: build.query<PrivacyAssessmentConfigResponse, void>({
      query: () => ({
        url: "plus/privacy-assessments/config",
      }),
      providesTags: ["Privacy Assessment Config"],
    }),

    updateAssessmentConfig: build.mutation<
      PrivacyAssessmentConfigResponse,
      PrivacyAssessmentConfigUpdate
    >({
      query: (body) => ({
        url: "plus/privacy-assessments/config",
        method: "PUT",
        body,
      }),
      invalidatesTags: ["Privacy Assessment Config"],
    }),

    getAssessmentConfigDefaults: build.query<
      PrivacyAssessmentConfigDefaults,
      void
    >({
      query: () => ({
        url: "plus/privacy-assessments/config/defaults",
      }),
    }),

    // PDF Report Download
    downloadAssessmentReport: build.mutation<void, string>({
      query: (id) => ({
        url: `plus/privacy-assessments/${id}/pdf?export_mode=external`,
        method: "GET",
        responseHandler: async (response) => {
          // Check for HTTP errors before treating response as PDF
          if (!response.ok) {
            let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
            try {
              const errorBody = await response.text();
              const errorJson = JSON.parse(errorBody);
              errorMessage =
                errorJson.detail || errorJson.message || errorMessage;
            } catch {
              // If error body isn't JSON, use the default HTTP error message
            }
            throw new Error(errorMessage);
          }

          const contentDisposition = response.headers.get(
            "content-disposition",
          );
          let filename = "assessment-report.pdf";

          if (contentDisposition) {
            // Try to extract filename from content-disposition header
            // Handles both: filename="name.pdf" and filename=name.pdf
            const match = contentDisposition.match(/filename="?([^";\n]+)"?/);
            if (match && match[1]) {
              filename = match[1].trim();
            }
          }

          const arrayBuffer = await response.arrayBuffer();
          const blob = new Blob([arrayBuffer], {
            type: response.headers.get("content-type") || "application/pdf",
          });
          saveAs(blob, filename);
          return { data: undefined };
        },
      }),
    }),

    // ── Questionnaire chat ──────────────────────────────────────

    startQuestionnaireChat: build.mutation<StartChatResponse, StartChatRequest>(
      {
        query: (body) => ({
          url: "plus/chat/questionnaire/start",
          method: "POST",
          body,
        }),
        invalidatesTags: ["Privacy Assessment"],
        async onQueryStarted(
          { assessment_id },
          { dispatch, queryFulfilled },
        ) {
          try {
            const { data } = await queryFulfilled;
            dispatch(
              privacyAssessmentsApi.util.updateQueryData(
                "getPrivacyAssessment",
                assessment_id,
                (draft) => {
                  if (draft.questionnaire) {
                    draft.questionnaire.status =
                      QuestionnaireSessionStatus.IN_PROGRESS;
                    draft.questionnaire.questionnaire_id =
                      data.questionnaire_id;
                    draft.questionnaire.answered_questions = 0;
                    draft.questionnaire.total_questions =
                      data.total_questions;
                  } else {
                    draft.questionnaire = {
                      questionnaire_id: data.questionnaire_id,
                      status: QuestionnaireSessionStatus.IN_PROGRESS,
                      stop_reason: null,
                      sent_at: new Date().toISOString(),
                      channel: "fides",
                      total_questions: data.total_questions,
                      answered_questions: 0,
                      last_reminder_at: null,
                      reminder_count: 0,
                    };
                  }
                },
              ),
            );
          } catch {
            // refetch will reconcile
          }
        },
      },
    ),

    sendQuestionnaireChatReply: build.mutation<
      ChatReplyResponse,
      ChatReplyRequest
    >({
      query: ({ assessment_id: _, ...body }) => ({
        url: "plus/chat/questionnaire/reply",
        method: "POST",
        body,
      }),
      async onQueryStarted({ assessment_id }, { dispatch, queryFulfilled }) {
        try {
          const { data } = await queryFulfilled;
          dispatch(
            privacyAssessmentsApi.util.updateQueryData(
              "getPrivacyAssessment",
              assessment_id,
              (draft) => {
                if (draft.questionnaire) {
                  draft.questionnaire.status = data.status as QuestionnaireSessionStatus;
                  draft.questionnaire.answered_questions =
                    data.answered_questions;
                  draft.questionnaire.total_questions = data.total_questions;
                }
              },
            ),
          );
        } catch {
          // refetch will reconcile on next poll
        }
      },
    }),

    getQuestionnaireChatMessages: build.query<
      QuestionnaireChatMessage[],
      string
    >({
      query: (questionnaireId) => ({
        url: `plus/chat/questionnaire/messages/${questionnaireId}`,
      }),
    }),
  }),
});

export const {
  useGetPrivacyAssessmentsQuery,
  useGetAssessmentTemplatesQuery,
  useGetPrivacyAssessmentQuery,
  useCreatePrivacyAssessmentMutation,
  useUpdatePrivacyAssessmentMutation,
  useDeletePrivacyAssessmentMutation,
  useUpdateAssessmentAnswerMutation,
  useBulkUpdateAssessmentAnswersMutation,
  useGetAssessmentEvidenceQuery,
  useCreateQuestionnaireMutation,
  useGetQuestionnaireStatusQuery,
  useCreateQuestionnaireReminderMutation,
  // Assessment Configuration
  useGetAssessmentConfigQuery,
  useUpdateAssessmentConfigMutation,
  useGetAssessmentConfigDefaultsQuery,
  // PDF Report
  useDownloadAssessmentReportMutation,
  // Assessment Tasks
  useGetAssessmentTasksQuery,
  // Questionnaire Chat
  useStartQuestionnaireChatMutation,
  useSendQuestionnaireChatReplyMutation,
  useGetQuestionnaireChatMessagesQuery,
} = privacyAssessmentsApi;

export { privacyAssessmentsApi };
