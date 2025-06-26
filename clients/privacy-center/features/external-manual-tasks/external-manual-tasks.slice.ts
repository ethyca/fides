/**
 * COPIED & ADAPTED FROM: clients/admin-ui/src/features/manual-tasks/manual-tasks.slice.ts
 *
 * Key differences for external users:
 * - Uses privacy-center's base API instead of admin-ui's baseApi
 * - Simplified filtering (no assignee filter, always filtered to current user)
 * - Uses external store instead of admin-ui store
 * - Uses external types instead of admin-ui types
 *
 * IMPORTANT: When updating admin-ui manual-tasks.slice.ts, review this component for sync!
 */

import { createSlice } from "@reduxjs/toolkit";

import { baseApi } from "~/features/common/api.slice";

// Import mock data from fixtures
import mockTasksData from "../../cypress/fixtures/external-manual-tasks/user-tasks.json";
import {
  CompleteTaskPayload,
  ManualTask,
  PageManualTask,
  RequestType,
  SkipTaskPayload,
  TaskActionResponse,
  TaskStatus,
} from "./types";

// Use the mock data directly since it's already in the correct format
const mockApiResponse: PageManualTask = mockTasksData as PageManualTask;

// Check if we're in a test environment (Cypress)
const isTestEnvironment = () => {
  return (
    typeof window !== "undefined" &&
    (window.Cypress || process.env.NODE_ENV === "test")
  );
};

// Helper function to paginate and filter results for external users
const paginateAndFilterResults = (
  page: number = 1,
  size: number = 25,
  searchTerm?: string,
  status?: TaskStatus,
  requestType?: RequestType,
  systemName?: string,
): PageManualTask => {
  // Start with all tasks from the mock data (already filtered to current user)
  let filteredTasks = mockApiResponse.items;

  // Apply filters
  if (searchTerm) {
    const lowerSearchTerm = searchTerm.toLowerCase();
    filteredTasks = filteredTasks.filter(
      (task) =>
        task.name.toLowerCase().includes(lowerSearchTerm) ||
        task.description.toLowerCase().includes(lowerSearchTerm),
    );
  }

  if (status) {
    filteredTasks = filteredTasks.filter((task) => task.status === status);
  }

  if (requestType) {
    filteredTasks = filteredTasks.filter(
      (task) => task.privacy_request.request_type === requestType,
    );
  }

  if (systemName) {
    filteredTasks = filteredTasks.filter(
      (task) => task.system.name === systemName,
    );
  }

  // Calculate pagination
  const total = filteredTasks.length;
  const pages = Math.ceil(total / size);
  const startIndex = (page - 1) * size;
  const endIndex = Math.min(startIndex + size, total);
  const paginatedTasks = filteredTasks.slice(startIndex, endIndex);

  return {
    items: paginatedTasks,
    total,
    page,
    size,
    pages,
    filterOptions: mockApiResponse.filterOptions, // Always include filter options
  };
};

// Interface for task query parameters (simplified for external users)
interface ExternalTaskQueryParams {
  page?: number;
  size?: number;
  search?: string;
  status?: TaskStatus;
  requestType?: RequestType;
  systemName?: string;
}

// API endpoints
export const externalManualTasksApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getExternalTasks: build.query<
      PageManualTask,
      ExternalTaskQueryParams | void
    >({
      // Use real API call in test environment, mock otherwise
      ...(isTestEnvironment()
        ? {
            query: (params) => {
              const queryParams = params || { page: 1, size: 25 };
              const searchParams = new URLSearchParams();

              Object.entries(queryParams).forEach(([key, value]) => {
                if (value !== undefined && value !== null) {
                  searchParams.append(key, String(value));
                }
              });

              return {
                url: "manual-tasks",
                params: searchParams,
              };
            },
          }
        : {
            queryFn: (params) => {
              // Set default values if params is undefined
              const queryParams = params || { page: 1, size: 25 };

              // Extract pagination parameters
              const {
                page = 1,
                size = 25,
                search,
                status,
                requestType,
                systemName,
              } = queryParams;

              // Return paginated and filtered results
              return {
                data: paginateAndFilterResults(
                  page,
                  size,
                  search,
                  status,
                  requestType,
                  systemName,
                ),
              };
            },
          }),
      providesTags: () => [{ type: "External Manual Tasks" }],
    }),

    completeExternalTask: build.mutation<
      TaskActionResponse,
      CompleteTaskPayload
    >({
      // Use real API call in test environment, mock otherwise
      ...(isTestEnvironment()
        ? {
            query: (payload) => ({
              url: `manual-tasks/${payload.task_id}/complete`,
              method: "POST",
              body: payload,
            }),
          }
        : {
            queryFn: (payload) => ({
              data: {
                task_id: payload.task_id,
                status: "completed" as TaskStatus,
              },
            }),
          }),
      invalidatesTags: [{ type: "External Manual Tasks" }],
    }),

    skipExternalTask: build.mutation<TaskActionResponse, SkipTaskPayload>({
      // Use real API call in test environment, mock otherwise
      ...(isTestEnvironment()
        ? {
            query: (payload) => ({
              url: `manual-tasks/${payload.task_id}/skip`,
              method: "POST",
              body: payload,
            }),
          }
        : {
            queryFn: (payload) => ({
              data: {
                task_id: payload.task_id,
                status: "skipped" as TaskStatus,
              },
            }),
          }),
      invalidatesTags: [{ type: "External Manual Tasks" }],
    }),

    getExternalTaskById: build.query<ManualTask, string>({
      // Use real API call in test environment, mock otherwise
      ...(isTestEnvironment()
        ? {
            query: (taskId) => `manual-tasks/${taskId}`,
          }
        : {
            queryFn: (taskId) => {
              const task = mockApiResponse.items.find(
                (t) => t.task_id === taskId,
              );
              return task
                ? { data: task }
                : {
                    error: {
                      status: 404,
                      data: { message: "Task not found" },
                    },
                  };
            },
          }),
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
