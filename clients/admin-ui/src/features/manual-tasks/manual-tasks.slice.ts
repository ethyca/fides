import { createSlice } from "@reduxjs/toolkit";

import { baseApi } from "~/features/common/api.slice";
import {
  CompleteTaskPayload,
  ManualTask,
  ManualTasksResponse,
  Page_ManualTask_,
  SkipTaskPayload,
  TaskActionResponse,
} from "~/types/api";
import {
  RequestType,
  TaskInputType,
  TaskStatus,
} from "~/types/api/models/ManualTask";
import { PaginationQueryParams } from "~/types/common/PaginationQueryParams";

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

// Helper function to paginate results
const paginateResults = (
  tasks: ManualTask[],
  page: number = 1,
  size: number = 10,
  searchTerm?: string,
): Page_ManualTask_ => {
  // Filter by search term if provided
  let filteredTasks = tasks;
  if (searchTerm) {
    const lowerSearchTerm = searchTerm.toLowerCase();
    filteredTasks = tasks.filter(
      (task) =>
        task.name.toLowerCase().includes(lowerSearchTerm) ||
        task.description.toLowerCase().includes(lowerSearchTerm),
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
    getTasks: build.query<Page_ManualTask_, TaskQueryParams | void>({
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

        // Filter tasks based on query parameters
        let filteredTasks = typedMockData.tasks;

        if (status) {
          filteredTasks = filteredTasks.filter(
            (task) => task.status === status,
          );
        }

        if (requestType) {
          filteredTasks = filteredTasks.filter(
            (task) => task.request_type === requestType,
          );
        }

        if (systemName) {
          filteredTasks = filteredTasks.filter(
            (task) => task.system_name === systemName,
          );
        }

        // Return paginated results
        return { data: paginateResults(filteredTasks, page, size, search) };
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

    getTaskById: build.query<ManualTask, string>({
      queryFn: (taskId) => {
        const task = typedMockData.tasks.find((t) => t.task_id === taskId);
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
  useGetTaskByIdQuery,
  useLazyGetTaskByIdQuery,
} = manualTasksApi;

// Slice for local state management
export const manualTasksSlice = createSlice({
  name: "manualTasks",
  initialState: {
    page: 1,
    pageSize: 10,
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
