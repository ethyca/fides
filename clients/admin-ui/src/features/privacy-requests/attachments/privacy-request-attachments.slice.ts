import { createSlice } from "@reduxjs/toolkit";

import { baseApi } from "~/features/common/api.slice";
import { AttachmentType } from "~/types/api/models/AttachmentType";
import { Page_AttachmentResponse_ } from "~/types/api/models/Page_AttachmentResponse_";

export interface State {}

const initialState: State = {};

interface GetAttachmentsParams {
  privacy_request_id: string;
  user_id: string;
  page?: number;
  size?: number;
}

interface UploadAttachmentParams {
  privacy_request_id: string;
  user_id: string;
  storage_key: string;
  attachment_type: AttachmentType;
  attachment_file: File;
}

const privacyRequestAttachmentsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAttachments: build.query<Page_AttachmentResponse_, GetAttachmentsParams>(
      {
        query: ({ privacy_request_id, user_id, page = 1, size }) => ({
          url: `plus/privacy-request/${privacy_request_id}/attachment`,
          method: "GET",
          params: {
            user_id,
            page,
            size,
          },
        }),
        providesTags: ["Privacy Request Attachments"],
      },
    ),
    uploadAttachment: build.mutation<void, UploadAttachmentParams>({
      query: ({
        privacy_request_id,
        user_id,
        storage_key,
        attachment_type,
        attachment_file,
      }) => {
        const formData = new FormData();
        formData.append("attachment_type", attachment_type);
        formData.append("attachment_file", attachment_file);

        return {
          url: `plus/privacy-request/${privacy_request_id}/attachment`,
          method: "POST",
          body: formData,
          params: {
            user_id,
            storage_key,
          },
        };
      },
      invalidatesTags: ["Privacy Request Attachments"],
    }),
  }),
});

export const { useGetAttachmentsQuery, useUploadAttachmentMutation } =
  privacyRequestAttachmentsApi;

export const privacyRequestAttachmentsSlice = createSlice({
  name: "privacyRequestAttachments",
  initialState,
  reducers: {},
});

export const { reducer } = privacyRequestAttachmentsSlice;
