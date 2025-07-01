import { createSlice } from "@reduxjs/toolkit";

import { baseApi } from "~/features/common/api.slice";
import {
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
        task_id: string;
        text_value?: string;
        checkbox_value?: boolean;
        attachment_type?: string;
        comment?: string;
      }
    >({
      query: (payload) => ({
        url: `plus/manual-fields/${payload.task_id}/complete`,
        method: "POST",
        body: payload,
      }),
      invalidatesTags: [{ type: "Manual Tasks" }],
    }),

    skipTask: build.mutation<
      { manual_field_id: string; status: ManualFieldStatus },
      { task_id: string; comment: string }
    >({
      query: (payload) => ({
        url: `plus/manual-fields/${payload.task_id}/skip`,
        method: "POST",
        body: payload,
      }),
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
