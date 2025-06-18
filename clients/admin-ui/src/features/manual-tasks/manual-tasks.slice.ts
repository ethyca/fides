import { createSlice } from "@reduxjs/toolkit";

import { baseApi } from "~/features/common/api.slice";
import {
  CompleteTaskPayload,
  ManualTask,
  ManualTasksResponse,
  SkipTaskPayload,
  TaskActionResponse,
} from "~/types/api";
import {
  RequestType,
  TaskInputType,
  TaskStatus,
} from "~/types/api/models/ManualTask";

// Import mock data
import mockTasksData from "./mocks/manual-tasks.json";

// Ensure mock data has correct types
const typedMockData: ManualTasksResponse = {
  tasks: mockTasksData.tasks.map((task) => ({
    ...task,
    input_type: task.input_type as TaskInputType,
    request_type: task.request_type as RequestType,
    status: task.status as TaskStatus,
  })),
};

// API endpoints
export const manualTasksApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getTasks: build.query<ManualTasksResponse, void>({
      queryFn: () => {
        // Return mock data
        return { data: typedMockData };
      },
      providesTags: () => [{ type: "Manual Tasks" }],
    }),

    completeTask: build.mutation<TaskActionResponse, CompleteTaskPayload>({
      queryFn: (payload) => {
        // Mock successful completion
        return {
          data: {
            task_id: payload.task_id,
            status: "completed" as TaskStatus,
          },
        };
      },
      invalidatesTags: [{ type: "Manual Tasks" }],
    }),

    skipTask: build.mutation<TaskActionResponse, SkipTaskPayload>({
      queryFn: (payload) => {
        // Mock successful skip
        return {
          data: {
            task_id: payload.task_id,
            status: "skipped" as TaskStatus,
          },
        };
      },
      invalidatesTags: [{ type: "Manual Tasks" }],
    }),

    getTaskById: build.query<ManualTask, string>({
      queryFn: (taskId) => {
        // Find task in mock data
        const task = typedMockData.tasks.find((t) => t.task_id === taskId);
        if (task) {
          return { data: task };
        }
        return {
          error: {
            status: 404,
            data: { message: "Task not found" },
          },
        };
      },
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
