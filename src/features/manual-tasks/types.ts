export type TaskStatus = "new" | "skipped" | "completed";
export type TaskInputType = "string" | "file" | "checkbox";
export type RequestType = "access" | "erasure";

export interface ManualTask {
  task_id: string;
  name: string;
  description: string;
  input_type: TaskInputType;
  request_type: RequestType;
  status: TaskStatus;
  assignedTo: string;
  privacy_request_id: string;
  created_at: string;
  updated_at: string;
  // Additional fields from linked privacy request
  days_left: number;
  due_date: string;
  // System information
  system_name: string;
  system_id: string;
}

export interface ManualTaskFilters {
  assignee?: string;
  status?: TaskStatus;
  request_type?: RequestType;
  system_id?: string;
  search?: string;
}

export interface CompleteTaskPayload {
  task_id: string;
  text_value?: string;
  checkbox_value?: boolean;
  attachment_type?: string;
  comment?: string;
}

export interface SkipTaskPayload {
  task_id: string;
  comment: string;
}

// API Response types
export interface ManualTasksResponse {
  tasks: ManualTask[];
}

export interface TaskActionResponse {
  task_id: string;
  status: TaskStatus;
}
