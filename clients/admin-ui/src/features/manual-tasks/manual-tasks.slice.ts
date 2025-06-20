import { createSlice } from "@reduxjs/toolkit";

import { baseApi } from "~/features/common/api.slice";
import { PaginationQueryParams } from "~/types/common/PaginationQueryParams";

// Import mock data and types
import mockTasksData from "./mocked/manual-tasks.json";
import {
  CompleteTaskPayload,
  ManualTask,
  PageManualTask,
  RequestType,
  SkipTaskPayload,
  TaskActionResponse,
  TaskStatus,
} from "./mocked/types";

// Use the mock data directly since it's already in the correct format
const mockApiResponse: PageManualTask = mockTasksData as PageManualTask;

// Helper function to paginate and filter results
const paginateAndFilterResults = (
  page: number = 1,
  size: number = 10,
  searchTerm?: string,
  status?: TaskStatus,
  requestType?: RequestType,
  systemName?: string,
): PageManualTask => {
  // Start with all tasks from the mock data
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

// Interface for task query parameters
interface TaskQueryParams extends PaginationQueryParams {
  search?: string;
  status?: TaskStatus;
  requestType?: RequestType;
  systemName?: string;
}

// API endpoints
export const manualTasksApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getTasks: build.query<PageManualTask, TaskQueryParams | void>({
      queryFn: (params) => {
        // Set default values if params is undefined
        const queryParams = params || { page: 1, size: 10 };

        // Extract pagination parameters
        const {
          page = 1,
          size = 10,
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
      providesTags: () => [{ type: "Manual Tasks" }],
    }),

    completeTask: build.mutation<TaskActionResponse, CompleteTaskPayload>({
      queryFn: (payload) => ({
        data: {
          task_id: payload.task_id,
          status: "completed" as TaskStatus,
        },
      }),
      invalidatesTags: [{ type: "Manual Tasks" }],
    }),

    skipTask: build.mutation<TaskActionResponse, SkipTaskPayload>({
      queryFn: (payload) => ({
        data: {
          task_id: payload.task_id,
          status: "skipped" as TaskStatus,
        },
      }),
      invalidatesTags: [{ type: "Manual Tasks" }],
    }),

    updateTaskAssignment: build.mutation<
      { task_id: string; assigned_users: any[]; updated_at: string },
      { taskId: string; assigned_user_ids: string[] }
    >({
      query: (payload) => ({
        url: `/manual-tasks/${payload.taskId}/assignment`,
        method: "PATCH",
        body: { assigned_user_ids: payload.assigned_user_ids },
      }),
      invalidatesTags: [{ type: "Manual Tasks" }],
    }),

    getTaskById: build.query<ManualTask, string>({
      queryFn: (taskId) => {
        const task = mockApiResponse.items.find((t) => t.task_id === taskId);
        return task
          ? { data: task }
          : {
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
  useUpdateTaskAssignmentMutation,
  useGetTaskByIdQuery,
  useLazyGetTaskByIdQuery,
} = manualTasksApi;

// Slice for local state management
export const manualTasksSlice = createSlice({
  name: "manualTasks",
  initialState: {
    page: 1,
    pageSize: 25, // Default to 25 instead of 10 to match PAGE_SIZES
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
