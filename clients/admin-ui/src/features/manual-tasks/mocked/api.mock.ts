import {
  CompleteTaskPayload,
  ManualTask,
  ManualTaskFilters,
  ManualTasksResponse,
  SkipTaskPayload,
  TaskActionResponse,
} from "../types";
import mockData from "./manual-tasks.json";
import { createMockTask } from "./types.mock";

// Helper function to simulate API delay
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// Helper function to filter tasks based on filters
const filterTasks = (
  tasks: ManualTask[],
  filters?: ManualTaskFilters,
): ManualTask[] => {
  if (!filters) return tasks;

  return tasks.filter((task) => {
    if (filters.assignee && task.assignedTo !== filters.assignee) return false;
    if (filters.status && task.status !== filters.status) return false;
    if (filters.request_type && task.request_type !== filters.request_type) {
      return false;
    }
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

// Cast the mock data to the correct type
const typedMockData = {
  tasks: mockData.tasks.map((task) => ({
    ...task,
    input_type: task.input_type as ManualTask["input_type"],
    request_type: task.request_type as ManualTask["request_type"],
    status: task.status as ManualTask["status"],
  })),
};

// Mock API functions
export const mockManualTasksApi = {
  // Get tasks with optional filters
  getTasks: async (
    filters?: ManualTaskFilters,
  ): Promise<ManualTasksResponse> => {
    await delay(500); // Simulate network delay
    const filteredTasks = filterTasks(typedMockData.tasks, filters);
    return { tasks: filteredTasks };
  },

  // Complete a task
  completeTask: async (
    payload: CompleteTaskPayload,
  ): Promise<TaskActionResponse> => {
    await delay(300);
    return {
      task_id: payload.task_id,
      status: "completed",
    };
  },

  // Skip a task
  skipTask: async (payload: SkipTaskPayload): Promise<TaskActionResponse> => {
    await delay(300);
    return {
      task_id: payload.task_id,
      status: "skipped",
    };
  },

  // Get a single task by ID
  getTaskById: async (taskId: string): Promise<ManualTask> => {
    await delay(300);
    const task = typedMockData.tasks.find((t) => t.task_id === taskId);
    if (!task) {
      throw new Error(`Task with ID ${taskId} not found`);
    }
    return task;
  },
};
