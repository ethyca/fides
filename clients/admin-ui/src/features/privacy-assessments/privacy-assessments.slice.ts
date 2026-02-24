import { baseApi } from "~/features/common/api.slice";
import type {
  CreateAssessmentRequest,
  Page_TemplateResponse_,
} from "~/types/api";

import {
  AssessmentEvidenceResponse,
  BulkUpdateAnswersRequest,
  BulkUpdateAnswersResponse,
  CreatePrivacyAssessmentResponse,
  GetAssessmentEvidenceParams,
  GetPrivacyAssessmentsParams,
  Page_PrivacyAssessmentResponse_,
  PrivacyAssessmentDetailResponse,
  PrivacyAssessmentResponse,
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
      CreatePrivacyAssessmentResponse,
      CreateAssessmentRequest
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
} = privacyAssessmentsApi;

export { privacyAssessmentsApi };
