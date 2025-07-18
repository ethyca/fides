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
  submission_user?: ManualFieldUser | null;
  comments?: Array<CommentResponse>;
  attachments?: Array<AttachmentResponse>;
  created_at: string;
  updated_at: string;
};
