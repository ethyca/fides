/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AttachmentResponse } from "./AttachmentResponse";
import type { CommentResponse } from "./CommentResponse";
import type { ManualFieldPrivacyRequest } from "./ManualFieldPrivacyRequest";
import type { ManualFieldRequestType } from "./ManualFieldRequestType";
import type { ManualFieldStatus } from "./ManualFieldStatus";
import type { ManualFieldSystem } from "./ManualFieldSystem";
import type { ManualFieldUser } from "./ManualFieldUser";
import type { ManualTaskFieldType } from "./ManualTaskFieldType";

/**
 * Single row returned by the search endpoint.
 */
export type ManualFieldListItem = {
  /**
   * Unique identifier for the manual field instance
   */
  manual_field_id: string;
  name: string;
  description?: string | null;
  input_type: ManualTaskFieldType;
  request_type: ManualFieldRequestType;
  status: ManualFieldStatus;
  assigned_users?: Array<ManualFieldUser>;
  privacy_request: ManualFieldPrivacyRequest;
  system?: ManualFieldSystem | null;
  created_at: string;
  updated_at: string;
  /**
   * Completion fields - populated when status is COMPLETED or SKIPPED
   */
  completed_by_user_id?: string | null;
  completed_by_user_first_name?: string | null;
  completed_by_user_last_name?: string | null;
  completed_by_user_email_address?: string | null;
  completion_comment?: CommentResponse | null;
  completion_attachment?: AttachmentResponse | null;
  completed_at?: string | null;
  /**
   * The field value submitted when completing the task
   */
  field_value?: string | null;
};
