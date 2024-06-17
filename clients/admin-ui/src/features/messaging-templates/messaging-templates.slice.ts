import { baseApi } from "~/features/common/api.slice";
import {
  MessagingTemplateWithPropertiesSummary,
  Page_MessagingTemplateWithPropertiesSummary_,
} from "~/types/api";
import { BulkUpdateFailed } from "~/types/api/models/BulkUpdateFailed";

export type MessagingTemplate = {
  type: string;
  label: string;
  content: {
    subject: string;
    body: string;
  };
};

export type BulkPutMessagingTemplateResponse = {
  succeeded: MessagingTemplate[];
  failed: BulkUpdateFailed[];
};

// Messaging Templates API
const messagingTemplatesApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getMessagingTemplates: build.query<MessagingTemplate[], void>({
      query: () => ({ url: `messaging/templates` }),
      providesTags: () => ["Messaging Templates"],
    }),
    getSummaryMessagingTemplates: build.query<
      Page_MessagingTemplateWithPropertiesSummary_,
      void
    >({
      query: () => ({ url: `messaging/templates/summary` }),
      providesTags: () => ["Messaging Templates"],
    }),
    updateMessagingTemplates: build.mutation<
      BulkPutMessagingTemplateResponse,
      MessagingTemplate[]
    >({
      query: (templates) => ({
        url: `messaging/templates`,
        method: "PUT",
        body: templates,
      }),
      invalidatesTags: () => ["Messaging Templates"],
    }),
  }),
});

export const {
  useGetMessagingTemplatesQuery,
  useUpdateMessagingTemplatesMutation,
  useGetSummaryMessagingTemplatesQuery,
} = messagingTemplatesApi;
