import { createSlice } from "@reduxjs/toolkit";

import { baseApi } from "~/features/common/api.slice";
import {
  AttachmentType,
  Body_skip_single_manual_field_api_v1_privacy_request__privacy_request_id__connection__connection_key__manual_field_skip_post,
  Body_submit_single_manual_field_api_v1_privacy_request__privacy_request_id__connection__connection_key__manual_field_complete_post,
  CommentType,
  ManualFieldListItem,
  ManualFieldRequestType,
  ManualFieldSearchResponse,
  ManualFieldStatus,
} from "~/types/api";
import { PaginationQueryParams } from "~/types/common/PaginationQueryParams";

import { PAGE_SIZES } from "../common/table/v2";

// Interface for task query parameters
interface TaskQueryParams extends PaginationQueryParams {
  search?: string;
  status?: ManualFieldStatus;
  requestType?: ManualFieldRequestType;
  systemName?: string;
  assignedUserId?: string;
}

// API endpoints
export const manualTasksApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getTasks: build.query<ManualFieldSearchResponse, TaskQueryParams | void>({
      query: (params) => {
        const queryParams = params || { page: 1, size: 10 };
        const searchParams = new URLSearchParams();

        // Convert page to be 1-indexed for API
        const page = queryParams.page || 1;
        searchParams.append("page", String(page));
        searchParams.append("size", String(queryParams.size || 10));

        if (queryParams.search) {
          searchParams.append("search", queryParams.search);
        }
        if (queryParams.status) {
          searchParams.append("status", queryParams.status);
        }
        if (queryParams.requestType) {
          searchParams.append("request_type", queryParams.requestType);
        }
        if (queryParams.systemName) {
          searchParams.append("system_name", queryParams.systemName);
        }
        if (queryParams.assignedUserId) {
          searchParams.append("assigned_user_id", queryParams.assignedUserId);
        }

        return {
          url: "plus/manual-fields",
          params: searchParams,
        };
      },
      providesTags: () => [{ type: "Manual Tasks" }],
    }),

    completeTask: build.mutation<
      { manual_field_id: string; status: ManualFieldStatus },
      {
        privacy_request_id: string;
        manual_field_id: string;
      } & Body_submit_single_manual_field_api_v1_privacy_request__privacy_request_id__connection__connection_key__manual_field_complete_post
    >({
      query: (payload) => {
        const {
          privacy_request_id: privacyRequestId,
          manual_field_id: manualFieldId,
          field_value: fieldValue,
          comment_text: commentText,
          attachment,
          ...rest
        } = payload;

        const formData = new FormData();

        // Append field_value if provided
        if (fieldValue !== undefined && fieldValue !== null) {
          formData.append("field_value", fieldValue);
        }

        // Append comment fields if provided
        if (commentText) {
          formData.append("comment_text", commentText);
          formData.append("comment_type", CommentType.NOTE);
        }

        // Append attachment fields if provided
        if (attachment) {
          formData.append("attachment", attachment);
          formData.append(
            "attachment_type",
            AttachmentType.INCLUDE_WITH_ACCESS_PACKAGE,
          );
        }

        // Append any other fields from rest
        Object.entries(rest).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            formData.append(key, String(value));
          }
        });

        return {
          url: `privacy-request/${privacyRequestId}/manual-field/${manualFieldId}/complete`,
          method: "POST",
          body: formData,
        };
      },
      invalidatesTags: [{ type: "Manual Tasks" }],
    }),

    skipTask: build.mutation<
      { manual_field_id: string; status: ManualFieldStatus },
      {
        privacy_request_id: string;
        manual_field_id: string;
      } & Body_skip_single_manual_field_api_v1_privacy_request__privacy_request_id__connection__connection_key__manual_field_skip_post
    >({
      query: (payload) => {
        const {
          privacy_request_id: privacyRequestId,
          manual_field_id: manualFieldId,
          ...body
        } = payload;
        return {
          url: `privacy-request/${privacyRequestId}/manual-field/${manualFieldId}/skip`,
          method: "POST",
          body: {
            ...body,
            field_key: manualFieldId,
            comment_type: body.comment_text ? CommentType.NOTE : undefined,
          },
        };
      },
      invalidatesTags: [{ type: "Manual Tasks" }],
    }),

    getTaskById: build.query<ManualFieldListItem, string>({
      query: (taskId) => `plus/manual-fields/${taskId}`,
      providesTags: (_result, _error, taskId) => [
        { type: "Manual Tasks", id: taskId },
      ],
    }),
  }),
});

// Export hooks
export const {
  useGetTasksQuery,
  useCompleteTaskMutation,
  useSkipTaskMutation,
  useGetTaskByIdQuery,
  useLazyGetTaskByIdQuery,
} = manualTasksApi;

// Slice for local state management
export const manualTasksSlice = createSlice({
  name: "manualTasks",
  initialState: {
    page: 1,
    pageSize: PAGE_SIZES[0],
  },
  reducers: {
    setPage: (state, action) => {
      return { ...state, page: action.payload };
    },
    setPageSize: (state, action) => {
      return { ...state, pageSize: action.payload };
    },
  },
});

// Export actions
export const { setPage, setPageSize } = manualTasksSlice.actions;

// Reducer
export const { reducer } = manualTasksSlice;
