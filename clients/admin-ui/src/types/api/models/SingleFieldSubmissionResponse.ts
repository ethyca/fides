/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AttachmentResponse } from "./AttachmentResponse";
import type { CommentResponse } from "./CommentResponse";

/**
 * Response schema for single field submission
 */
export type SingleFieldSubmissionResponse = {
  privacy_request_id: string;
  connection_key: string;
  field_key: string;
  /**
   * The field value (may be empty if attachment was provided)
   */
  field_value: string;
  submission_id: string;
  instance_id: string;
  instance_status: string;
  is_complete: boolean;
  completed_at?: string | null;
  comment?: CommentResponse | null;
  attachment?: AttachmentResponse | null;
  message: string;
  user_id?: string | null;
  user_first_name?: string | null;
  user_last_name?: string | null;
  user_email_address?: string | null;
};
