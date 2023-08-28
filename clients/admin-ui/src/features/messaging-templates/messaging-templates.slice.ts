import { baseApi } from "~/features/common/api.slice";
import { BulkUpdateFailed } from "~/types/api/models/BulkUpdateFailed";

export type MessagingTemplate = {
  key: string;
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
      query: () => ({ url: `messaging/templates/` }),
      providesTags: () => ["Messaging Templates"],
    }),
    updateMessagingTemplates: build.mutation<
      BulkPutMessagingTemplateResponse,
      MessagingTemplate[]
    >({
      query: (templates) => ({
        url: `messaging/templates/`,
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
} = messagingTemplatesApi;
