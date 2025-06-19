export type TaskStatus = "new" | "completed" | "skipped";
export type TaskInputType = "string" | "file" | "checkbox";
export type RequestType = "access" | "erasure";

export interface AssignedUser {
  id: string;
  email_address: string;
  first_name: string;
  last_name: string;
}

export interface SubjectIdentity {
  email?: {
    label: string;
    value: string;
  };
  phone_number?: {
    label: string;
    value: string;
  };
}

export interface PrivacyRequest {
  id: string;
  days_left: number;
  subject_identity: SubjectIdentity;
  request_type: RequestType;
}

export interface System {
  id: string;
  name: string;
}

export interface ManualTask {
  task_id: string;
  name: string;
  description: string;
  status: TaskStatus;
  assigned_users: AssignedUser[];
  input_type?: "string" | "checkbox";
  privacy_request: PrivacyRequest;
  system: System;
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

// Pagination type for manual tasks
export interface PageManualTask {
  items: ManualTask[];
  total: number | null;
  page: number | null;
  size: number | null;
  pages?: number | null;
}

export interface TaskQueryParams {
  page?: number;
  size?: number;
  status?: TaskStatus;
  request_type?: RequestType;
  system_name?: string;
  search?: string;
  assigned_user_id?: string;
}
