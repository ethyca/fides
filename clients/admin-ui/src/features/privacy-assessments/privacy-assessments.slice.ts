import { baseApi } from "~/features/common/api.slice";

import {
  AssessmentEvidenceResponse,
  BulkUpdateAnswersRequest,
  BulkUpdateAnswersResponse,
  CreatePrivacyAssessmentRequest,
  CreatePrivacyAssessmentResponse,
  CreateQuestionnaireRequest,
  CreateReminderRequest,
  GetAssessmentEvidenceParams,
  GetPrivacyAssessmentsParams,
  Page_PrivacyAssessmentResponse_,
  PrivacyAssessmentDetailResponse,
  PrivacyAssessmentResponse,
  QuestionnaireResponse,
  QuestionnaireStatusResponse,
  ReminderResponse,
  UpdateAnswerRequest,
  UpdateAnswerResponse,
  UpdatePrivacyAssessmentRequest,
} from "./types";

const privacyAssessmentsApi = baseApi.injectEndpoints({
  overrideExisting: true,
  endpoints: (build) => ({
    getPrivacyAssessments: build.query<
      Page_PrivacyAssessmentResponse_,
      GetPrivacyAssessmentsParams | void
    >({
      query: (params) => ({
        url: "plus/privacy-assessments",
        params: params ?? undefined,
      }),
      providesTags: ["Privacy Assessment"],
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
      CreatePrivacyAssessmentResponse,
      CreatePrivacyAssessmentRequest
    >({
      query: (body) => ({
        url: "plus/privacy-assessments",
        method: "POST",
        body,
      }),
      invalidatesTags: ["Privacy Assessment"],
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
        url: `plus/privacy-assessments/${id}/answers/${questionId}`,
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
        url: `plus/privacy-assessments/${id}/answers`,
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
  }),
});

export const {
  useGetPrivacyAssessmentsQuery,
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
} = privacyAssessmentsApi;

export { privacyAssessmentsApi };
