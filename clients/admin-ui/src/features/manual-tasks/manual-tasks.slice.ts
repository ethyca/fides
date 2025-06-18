import { createSlice } from "@reduxjs/toolkit";

import { baseApi } from "~/features/common/api.slice";
import {
  CompleteTaskPayload,
  ManualTask,
  ManualTasksResponse,
  SkipTaskPayload,
  TaskActionResponse,
} from "~/types/api";

// API endpoints
export const manualTasksApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getTasks: build.query<ManualTasksResponse, void>({
      query: () => ({
        url: "plus/manual-tasks",
        method: "GET",
      }),
      providesTags: () => [{ type: "Manual Tasks" }],
    }),

    completeTask: build.mutation<TaskActionResponse, CompleteTaskPayload>({
      query: (payload) => ({
        url: `plus/manual-tasks/${payload.task_id}/complete`,
        method: "POST",
        body: payload,
      }),
      invalidatesTags: [{ type: "Manual Tasks" }],
    }),

    skipTask: build.mutation<TaskActionResponse, SkipTaskPayload>({
      query: (payload) => ({
        url: `plus/manual-tasks/${payload.task_id}/skip`,
        method: "POST",
        body: payload,
      }),
      invalidatesTags: [{ type: "Manual Tasks" }],
    }),

    getTaskById: build.query<ManualTask, string>({
      query: (taskId) => ({
        url: `plus/manual-tasks/${taskId}`,
        method: "GET",
      }),
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
  initialState: {},
  reducers: {},
});

// Reducer
export const { reducer } = manualTasksSlice;
