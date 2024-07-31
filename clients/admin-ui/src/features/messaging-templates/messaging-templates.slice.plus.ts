import { baseApi } from "common/api.slice";

import {
  MessagingTemplateCreate,
  MessagingTemplatePatch,
  MessagingTemplateResponse,
  MessagingTemplateUpdate,
} from "~/features/messaging-templates/messaging-templates.slice";
import { Page_MessagingTemplateWithPropertiesSummary_ } from "~/types/api";

const messagingTemplatesPlusApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getSummaryMessagingTemplates: build.query<
      Page_MessagingTemplateWithPropertiesSummary_,
      any
    >({
      query: (params) => ({
        method: "GET",
        url: `plus/messaging/templates/summary`,
        params,
      }),
      providesTags: () => ["Property-Specific Messaging Templates"],
    }),
    // Full update existing template
    putMessagingTemplateById: build.mutation<
      MessagingTemplateResponse,
      MessagingTemplateUpdate
    >({
      query: ({ templateId, template }) => ({
        url: `plus/messaging/templates/${templateId}`,
        method: "PUT",
        body: template,
      }),
      invalidatesTags: () => ["Property-Specific Messaging Templates"],
    }),
    // Partial update existing template, e.g. enable it
    patchMessagingTemplateById: build.mutation<
      MessagingTemplateResponse,
      MessagingTemplatePatch
    >({
      query: ({ templateId, template }) => ({
        url: `plus/messaging/templates/${templateId}`,
        method: "PATCH",
        body: template,
      }),
      invalidatesTags: () => ["Property-Specific Messaging Templates"],
    }),
    // endpoint for creating new messaging template- POST by type
    createMessagingTemplateByType: build.mutation<
      MessagingTemplateResponse,
      MessagingTemplateCreate
    >({
      query: ({ templateType, template }) => ({
        url: `plus/messaging/templates/${templateType}`,
        method: "POST",
        body: template,
      }),
      invalidatesTags: () => ["Property-Specific Messaging Templates"],
    }),
  }),
});

export const {
  useGetSummaryMessagingTemplatesQuery,
  usePutMessagingTemplateByIdMutation,
  useCreateMessagingTemplateByTypeMutation,
  usePatchMessagingTemplateByIdMutation,
} = messagingTemplatesPlusApi;
