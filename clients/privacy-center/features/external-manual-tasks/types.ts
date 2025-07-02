/**
 * Types for External Manual Tasks feature
 *
 * COPIED & ADAPTED FROM: clients/admin-ui/src/features/manual-tasks/types.ts
 * Key differences for external users:
 * - Simplified auth flow (no complex user management)
 * - Always filtered to current external user
 * - No admin-specific properties
 */

// Re-export enums from existing external-manual-tasks slice
export {
  ManualFieldRequestType,
  ManualFieldStatus,
  ManualTaskFieldType,
} from "./external-manual-tasks.slice";

// Authentication Types
export interface ExternalAuthState {
  isAuthenticated: boolean;
  token: string | null;
  user: ExternalUser | null;
  emailToken: string | null;
  isLoading: boolean;
  error: string | null;
}

export interface ExternalUser {
  id: string;
  username: string;
  created_at: string;
  email_address: string;
  first_name: string;
  last_name: string;
  disabled: boolean;
  disabled_reason: string;
}

export interface OtpRequestPayload {
  email: string;
  email_token: string;
}

export interface OtpRequestResponse {
  message: string;
  email: string;
}

export interface OtpVerifyPayload {
  email: string;
  otp_code: string;
}

export interface OtpVerifyResponse {
  user_data: ExternalUser;
  token_data: {
    access_token: string;
  };
}

// Manual Tasks Types (simplified from admin-ui)
export interface ExternalManualTask {
  task_id: string;
  name: string;
  description: string;
  input_type: "file" | "string" | "checkbox";
  status: "new" | "in_progress" | "completed" | "skipped";
  assigned_users: ExternalUser[];
  privacy_request: {
    id: string;
    days_left: number;
    request_type: "access" | "erasure";
    subject_identities: Record<string, string>;
  };
  system: {
    id: string;
    name: string;
  };
}

export interface TaskCompletionPayload {
  text_value?: string;
  checkbox_value?: boolean;
  comment?: string;
  attachment_type?: "file";
}

export interface TaskSkipPayload {
  comment: string;
}

// API Response Types
export interface ExternalTasksResponse {
  items: ExternalManualTask[];
  total: number;
  page: number;
  size: number;
  pages: number;
  filterOptions: {
    systems: Array<{ id: string; name: string }>;
    assigned_users: ExternalUser[];
  };
}

// Component Props Types
export interface OtpRequestFormProps {
  emailToken: string;
  onRequestOtp: (email: string) => Promise<void>;
  initialEmail?: string;
  isLoading?: boolean;
  error?: string | null;
}

export interface OtpVerificationFormProps {
  emailToken: string;
  enteredEmail: string;
  onVerifyOtp: (otpCode: string) => Promise<void>;
  onBack: () => void;
  isLoading?: boolean;
  error?: string | null;
}

export interface ExternalTaskLayoutProps {
  user: ExternalUser;
  onLogout: () => void;
  children: React.ReactNode;
}

// Task management types (added for Phase 3)
export type TaskStatus = "new" | "completed" | "skipped";
export type TaskInputType = "string" | "file" | "checkbox";
export type RequestType = "access" | "erasure";

export interface System {
  id: string;
  name: string;
}

export interface AssignedUser {
  id: string;
  first_name: string;
  last_name: string;
  email_address: string;
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
  request_type: RequestType;
  subject_identities?: Record<string, string>;
}

export interface ManualTask {
  task_id: string;
  name: string;
  description: string;
  status: TaskStatus;
  assigned_users: AssignedUser[];
  input_type?: TaskInputType;
  privacy_request: PrivacyRequest;
  system: System;
}

export interface FilterOptions {
  systems?: System[];
  assigned_users?: AssignedUser[];
}

export interface PageManualTask {
  items: ManualTask[];
  total: number | null;
  page: number | null;
  size: number | null;
  pages?: number | null;
  filterOptions?: FilterOptions;
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

export interface TaskActionResponse {
  task_id: string;
  status: TaskStatus;
}
