import { createSlice } from "@reduxjs/toolkit";
import { baseApi } from "~/features/common/api.slice";

export type MessagingTemplate = {
  key: string;
  content: {
    subject: string;
    body: string;
  };
};

// Messaging Templates API
const messagingTemplatesApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getMessagingTemplates: build.query<MessagingTemplate[], void>({
      query: () => ({ url: `messaging/templates` }),
      providesTags: () => ["Messaging Templates"],
    }),
    updateMessagingTemplates: build.mutation<string, MessagingTemplate[]>({
      query: (customization) => ({
        url: `messaging/templates`,
        method: "POST",
        body: customization,
      }),
      invalidatesTags: () => ["Messaging Templates"],
    }),
  }),
});

export const {
  useGetMessagingTemplatesQuery,
  useUpdateMessagingTemplatesMutation,
} = messagingTemplatesApi;

export const messagingTemplatesSlice = createSlice({
  name: "messagingTemplates",
  initialState: {},
  reducers: {},
});

export const { reducer } = messagingTemplatesSlice;
