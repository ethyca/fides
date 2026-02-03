/**
 * Privacy Assessments API Slice
 *
 * RTK Query API slice for privacy assessment endpoints.
 * Provides hooks for fetching, creating, updating, and deleting assessments,
 * as well as managing questionnaires and evidence.
 */

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

// Tag types for cache invalidation (must match baseApi tagTypes)
const PRIVACY_ASSESSMENT_TAG = "Privacy Assessment" as const;
const QUESTIONNAIRE_TAG = "Questionnaire" as const;
const EVIDENCE_TAG = "Evidence" as const;

const privacyAssessmentsApi = baseApi.injectEndpoints({
  overrideExisting: true,
  endpoints: (build) => ({
    /**
     * List all privacy assessments with pagination
     * GET /plus/privacy-assessments
     */
    getPrivacyAssessments: build.query<
      Page_PrivacyAssessmentResponse_,
      GetPrivacyAssessmentsParams | void
    >({
      query: (params) => ({
        url: "plus/privacy-assessments",
        params: params ?? undefined,
      }),
      providesTags: [PRIVACY_ASSESSMENT_TAG],
    }),

    /**
     * Get a single privacy assessment with full question groups and answers
     * GET /plus/privacy-assessments/{id}
     */
    getPrivacyAssessment: build.query<PrivacyAssessmentDetailResponse, string>({
      query: (id) => ({
        url: `plus/privacy-assessments/${id}`,
      }),
      providesTags: (_result, _error, id) => [
        { type: PRIVACY_ASSESSMENT_TAG, id },
      ],
    }),

    /**
     * Create new privacy assessments by triggering generation
     * POST /plus/privacy-assessments
     */
    createPrivacyAssessment: build.mutation<
      CreatePrivacyAssessmentResponse,
      CreatePrivacyAssessmentRequest
    >({
      query: (body) => ({
        url: "plus/privacy-assessments",
        method: "POST",
        body,
      }),
      invalidatesTags: [PRIVACY_ASSESSMENT_TAG],
    }),

    /**
     * Update assessment metadata
     * PUT /plus/privacy-assessments/{id}
     */
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
        { type: PRIVACY_ASSESSMENT_TAG, id },
        PRIVACY_ASSESSMENT_TAG,
      ],
    }),

    /**
     * Delete an assessment
     * DELETE /plus/privacy-assessments/{id}
     */
    deletePrivacyAssessment: build.mutation<void, string>({
      query: (id) => ({
        url: `plus/privacy-assessments/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: [PRIVACY_ASSESSMENT_TAG],
    }),

    /**
     * Update a single question's answer
     * PUT /plus/privacy-assessments/{id}/answers/{questionId}
     */
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
        { type: PRIVACY_ASSESSMENT_TAG, id },
        PRIVACY_ASSESSMENT_TAG,
        { type: EVIDENCE_TAG, id },
      ],
    }),

    /**
     * Bulk update multiple answers
     * PUT /plus/privacy-assessments/{id}/answers
     */
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
        { type: PRIVACY_ASSESSMENT_TAG, id },
        PRIVACY_ASSESSMENT_TAG,
        { type: EVIDENCE_TAG, id },
      ],
    }),

    /**
     * Get all evidence for an assessment
     * GET /plus/privacy-assessments/{id}/evidence
     */
    getAssessmentEvidence: build.query<
      AssessmentEvidenceResponse,
      GetAssessmentEvidenceParams
    >({
      query: ({ id, ...params }) => ({
        url: `plus/privacy-assessments/${id}/evidence`,
        params,
      }),
      providesTags: (_result, _error, { id }) => [{ type: EVIDENCE_TAG, id }],
    }),

    /**
     * Create/send a questionnaire to the team
     * POST /plus/privacy-assessments/{id}/questionnaire
     */
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
        { type: QUESTIONNAIRE_TAG, id },
        { type: PRIVACY_ASSESSMENT_TAG, id },
      ],
    }),

    /**
     * Get questionnaire status and progress
     * GET /plus/privacy-assessments/{id}/questionnaire
     */
    getQuestionnaireStatus: build.query<QuestionnaireStatusResponse, string>({
      query: (id) => ({
        url: `plus/privacy-assessments/${id}/questionnaire`,
      }),
      providesTags: (_result, _error, id) => [{ type: QUESTIONNAIRE_TAG, id }],
    }),

    /**
     * Create a reminder for the questionnaire
     * POST /plus/privacy-assessments/{id}/questionnaire/reminders
     */
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
        { type: QUESTIONNAIRE_TAG, id },
      ],
    }),
  }),
});

// Export hooks for use in components
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

// Export the API for use in tests or other advanced scenarios
export { privacyAssessmentsApi };
