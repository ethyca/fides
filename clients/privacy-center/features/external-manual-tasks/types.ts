/**
 * Types for External Manual Tasks feature
 *
 * COPIED & ADAPTED FROM: clients/admin-ui/src/features/manual-tasks/types.ts
 * Key differences for external users:
 * - Simplified auth flow (no complex user management)
 * - Always filtered to current external user
 * - No admin-specific properties
 */

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
  email_address: string;
  first_name: string;
  last_name: string;
  disabled: boolean;
}

export interface OtpRequestPayload {
  email_token: string;
}

export interface OtpRequestResponse {
  message: string;
  email: string;
}

export interface OtpVerifyPayload {
  email_token: string;
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
    subject_identity: {
      [key: string]: {
        label: string;
        value: string;
      };
    };
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
  onOtpRequested: () => void;
  isLoading?: boolean;
  error?: string | null;
}

export interface OtpVerificationFormProps {
  emailToken: string;
  onOtpVerified: (response: OtpVerifyResponse) => void;
  onBack: () => void;
  isLoading?: boolean;
  error?: string | null;
}

export interface ExternalTaskLayoutProps {
  user: ExternalUser;
  onLogout: () => void;
  children: React.ReactNode;
}
