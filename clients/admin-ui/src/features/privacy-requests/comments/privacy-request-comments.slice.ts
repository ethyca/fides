import { createSlice } from "@reduxjs/toolkit";

import { baseApi } from "~/features/common/api.slice";
import { CommentResponse } from "~/types/api/models/CommentResponse";
import { CommentType } from "~/types/api/models/CommentType";
import { Page_CommentResponse_ } from "~/types/api/models/Page_CommentResponse_";

export interface State {}

const initialState: State = {};

interface GetCommentsParams {
  privacy_request_id: string;
  page?: number;
  size?: number;
}

interface CreateCommentParams {
  privacy_request_id: string;
  comment_text: string;
  comment_type: CommentType;
}

const privacyRequestCommentsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getComments: build.query<Page_CommentResponse_, GetCommentsParams>({
      query: ({ privacy_request_id, page = 1, size }) => ({
        url: `plus/privacy-request/${privacy_request_id}/comment`,
        method: "GET",
        params: {
          page,
          size,
        },
      }),
      providesTags: ["Privacy Request Comments"],
    }),
    createComment: build.mutation<CommentResponse, CreateCommentParams>({
      query: ({ privacy_request_id, comment_text, comment_type }) => {
        const formData = new FormData();
        formData.append("comment_text", comment_text);
        formData.append("comment_type", comment_type);

        return {
          url: `plus/privacy-request/${privacy_request_id}/comment`,
          method: "POST",
          body: formData,
          formData: true,
        };
      },
      invalidatesTags: ["Privacy Request Comments", "Request"],
    }),
    getCommentDetails: build.query<
      CommentResponse,
      { privacy_request_id: string; comment_id: string }
    >({
      query: ({ privacy_request_id, comment_id }) => ({
        url: `plus/privacy-request/${privacy_request_id}/comment/${comment_id}`,
        method: "GET",
      }),
    }),
  }),
});

export const {
  useGetCommentsQuery,
  useCreateCommentMutation,
  useGetCommentDetailsQuery,
  useLazyGetCommentDetailsQuery,
} = privacyRequestCommentsApi;

export const privacyRequestCommentsSlice = createSlice({
  name: "privacyRequestComments",
  initialState,
  reducers: {},
});

export const { reducer } = privacyRequestCommentsSlice;
