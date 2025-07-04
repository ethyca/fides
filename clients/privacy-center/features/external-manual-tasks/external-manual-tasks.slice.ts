/**
 * COPIED & ADAPTED FROM: clients/admin-ui/src/features/manual-tasks/manual-tasks.slice.ts
 *
 * Key differences for external users:
 * - Uses privacy-center's base API instead of admin-ui's baseApi
 * - Simplified filtering (no assignee filter, always filtered to current user)
 * - Uses external store instead of admin-ui store
 * - External user authentication context
 *
 * IMPORTANT: When updating admin-ui manual-tasks.slice.ts, review this component for sync!
 */

import { createSlice } from "@reduxjs/toolkit";

import { externalBaseApi } from "./external-base-api.slice";

// Import real API types - we'll need to make sure these are available in privacy-center
// For now, let's define the essential types locally based on the admin-ui implementation
export enum ManualFieldStatus {
  NEW = "new",
  COMPLETED = "completed",
  SKIPPED = "skipped",
}

export enum ManualFieldRequestType {
  ACCESS = "access",
  ERASURE = "erasure",
}

export enum ManualTaskFieldType {
  TEXT = "text",
  CHECKBOX = "checkbox",
  ATTACHMENT = "attachment",
}

export enum CommentType {
  NOTE = "note",
}

export enum AttachmentType {
  INCLUDE_WITH_ACCESS_PACKAGE = "include_with_access_package",
}

export interface ManualFieldUser {
  id: string;
  email_address?: string | null;
  first_name?: string | null;
  last_name?: string | null;
}

export interface ManualFieldSystem {
  id: string;
  name: string;
}

export interface IdentityField {
  label: string;
  value: string;
}

export interface ManualFieldPrivacyRequest {
  id: string;
  days_left?: number | null;
  request_type: ManualFieldRequestType;
  subject_identities?: Record<string, string> | null;
  custom_fields?: {
    [key: string]: string;
  };
}

export interface ManualFieldListItem {
  manual_field_id: string;
  name: string;
  description?: string | null;
  input_type: ManualTaskFieldType;
  request_type: ManualFieldRequestType;
  status: ManualFieldStatus;
  assigned_users?: ManualFieldUser[];
  privacy_request: ManualFieldPrivacyRequest;
  system?: ManualFieldSystem | null;
  created_at: string;
  updated_at: string;
}

export interface ManualFieldSearchFilterOptions {
  assigned_users?: ManualFieldUser[];
  systems?: ManualFieldSystem[];
}

export interface ManualFieldSearchResponse {
  items: ManualFieldListItem[];
  total: number;
  page: number;
  size: number;
  pages: number;
  filter_options: ManualFieldSearchFilterOptions;
}

// Interface for task query parameters (simplified for external users)
interface ExternalTaskQueryParams {
  page?: number;
  size?: number;
  status?: ManualFieldStatus;
  requestType?: ManualFieldRequestType;
  systemName?: string;
}

// API endpoints
export const externalManualTasksApi = externalBaseApi.injectEndpoints({
  endpoints: (build) => ({
    getExternalTasks: build.query<
      ManualFieldSearchResponse,
      ExternalTaskQueryParams | void
    >({
      query: (params) => {
        const queryParams = params || { page: 1, size: 25 };
        const searchParams = new URLSearchParams();

        // Convert page to be 1-indexed for API
        const page = queryParams.page || 1;
        searchParams.append("page", String(page));
        searchParams.append("size", String(queryParams.size || 25));

        if (queryParams.status) {
          searchParams.append("status", queryParams.status);
        }
        if (queryParams.requestType) {
          searchParams.append("request_type", queryParams.requestType);
        }
        if (queryParams.systemName) {
          searchParams.append("system_name", queryParams.systemName);
        }

        return {
          url: "plus/manual-fields",
          params: searchParams,
        };
      },
      providesTags: () => [{ type: "External Manual Tasks" }],
    }),

    completeExternalTask: build.mutation<
      { manual_field_id: string; status: ManualFieldStatus },
      {
        privacy_request_id: string;
        manual_field_id: string;
        field_value?: string;
        comment_text?: string;
        attachment?: File;
      }
    >({
      query: (payload) => {
        const {
          privacy_request_id: privacyRequestId,
          manual_field_id: manualFieldId,
          field_value: fieldValue,
          comment_text: commentText,
          attachment,
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

        return {
          url: `privacy-request/${privacyRequestId}/manual-field/${manualFieldId}/complete`,
          method: "POST",
          body: formData,
        };
      },
      invalidatesTags: [{ type: "External Manual Tasks" }],
    }),

    skipExternalTask: build.mutation<
      { manual_field_id: string; status: ManualFieldStatus },
      {
        privacy_request_id: string;
        manual_field_id: string;
        field_key: string;
        skip_reason: string;
      }
    >({
      query: (payload) => {
        const {
          privacy_request_id: privacyRequestId,
          manual_field_id: manualFieldId,
          field_key: fieldKey,
          skip_reason: skipReason,
        } = payload;

        const formData = new FormData();
        formData.append("field_key", fieldKey);
        formData.append("skip_reason", skipReason);
        formData.append("comment_text", skipReason);
        formData.append("comment_type", CommentType.NOTE);

        return {
          url: `privacy-request/${privacyRequestId}/manual-field/${manualFieldId}/skip`,
          method: "POST",
          body: formData,
        };
      },
      invalidatesTags: [{ type: "External Manual Tasks" }],
    }),

    getExternalTaskById: build.query<ManualFieldListItem, string>({
      query: (taskId) => `plus/manual-fields/${taskId}`,
      providesTags: (_result, _error, taskId) => [
        { type: "External Manual Tasks", id: taskId },
      ],
    }),
  }),
});

// Export hooks
export const {
  useGetExternalTasksQuery,
  useCompleteExternalTaskMutation,
  useSkipExternalTaskMutation,
  useGetExternalTaskByIdQuery,
  useLazyGetExternalTaskByIdQuery,
} = externalManualTasksApi;

// Slice for local state management (simplified for external users)
export const externalManualTasksSlice = createSlice({
  name: "externalManualTasks",
  initialState: {
    page: 1,
    pageSize: 25,
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
export const { setPage, setPageSize } = externalManualTasksSlice.actions;

// Reducer
export const { reducer: externalManualTasksReducer } = externalManualTasksSlice;
