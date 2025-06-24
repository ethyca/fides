import { createSlice, createAsyncThunk, PayloadAction } from "@reduxjs/toolkit";
import type { RootState } from "~/app/store";
import {
  ManualTask,
  ManualTaskFilters,
  CompleteTaskPayload,
  SkipTaskPayload,
  TaskActionResponse,
} from "./types";
import { mockManualTasksApi } from "./mocked/api.mock";

// State interface
interface ManualTasksState {
  tasks: ManualTask[];
  isLoading: boolean;
  error: string | null;
  filters: ManualTaskFilters;
}

// Initial state
const initialState: ManualTasksState = {
  tasks: [],
  isLoading: false,
  error: null,
  filters: {},
};

// Async thunks
export const fetchManualTasks = createAsyncThunk(
  "manualTasks/fetchTasks",
  async (filters?: ManualTaskFilters) => {
    const response = await mockManualTasksApi.getTasks(filters);
    return response.tasks;
  }
);

export const completeTask = createAsyncThunk(
  "manualTasks/complete",
  async (payload: CompleteTaskPayload) => {
    const response = await mockManualTasksApi.completeTask(payload);
    return response;
  }
);

export const skipTask = createAsyncThunk(
  "manualTasks/skip",
  async (payload: SkipTaskPayload) => {
    const response = await mockManualTasksApi.skipTask(payload);
    return response;
  }
);

// Slice
const manualTasksSlice = createSlice({
  name: "manualTasks",
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<ManualTaskFilters>) => {
      state.filters = action.payload;
    },
    clearFilters: (state) => {
      state.filters = {};
    },
  },
  extraReducers: (builder) => {
    // Fetch tasks
    builder
      .addCase(fetchManualTasks.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchManualTasks.fulfilled, (state, action) => {
        state.isLoading = false;
        state.tasks = action.payload;
      })
      .addCase(fetchManualTasks.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || "Failed to fetch tasks";
      });

    // Complete task
    builder
      .addCase(completeTask.fulfilled, (state, action) => {
        const { task_id, status } = action.payload;
        const task = state.tasks.find((t) => t.task_id === task_id);
        if (task) {
          task.status = status;
          task.updated_at = new Date().toISOString();
        }
      })
      .addCase(completeTask.rejected, (state, action) => {
        state.error = action.error.message || "Failed to complete task";
      });

    // Skip task
    builder
      .addCase(skipTask.fulfilled, (state, action) => {
        const { task_id, status } = action.payload;
        const task = state.tasks.find((t) => t.task_id === task_id);
        if (task) {
          task.status = status;
          task.updated_at = new Date().toISOString();
        }
      })
      .addCase(skipTask.rejected, (state, action) => {
        state.error = action.error.message || "Failed to skip task";
      });
  },
});

// Actions
export const { setFilters, clearFilters } = manualTasksSlice.actions;

// Selectors
export const selectManualTasks = (state: RootState) => state.manualTasks.tasks;
export const selectIsLoading = (state: RootState) =>
  state.manualTasks.isLoading;
export const selectError = (state: RootState) => state.manualTasks.error;
export const selectFilters = (state: RootState) => state.manualTasks.filters;

export const selectFilteredTasks = (state: RootState) => {
  const tasks = selectManualTasks(state);
  const filters = selectFilters(state);

  return tasks.filter((task) => {
    if (filters.assignee && task.assignedTo !== filters.assignee) return false;
    if (filters.status && task.status !== filters.status) return false;
    if (filters.request_type && task.request_type !== filters.request_type)
      return false;
    if (filters.system_id && task.system_id !== filters.system_id) return false;
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      return (
        task.name.toLowerCase().includes(searchLower) ||
        task.description.toLowerCase().includes(searchLower)
      );
    }
    return true;
  });
};

// Reducer
export default manualTasksSlice.reducer;
