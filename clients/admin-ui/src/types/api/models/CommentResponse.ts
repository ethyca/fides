/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AttachmentResponse } from "./AttachmentResponse";
import type { CommentType } from "./CommentType";

/**
 * Model for comment responses.
 */
export type CommentResponse = {
  /**
   * The comment ID
   */
  id: string;
  /**
   * The privacy request ID
   */
  privacy_request_id: string;
  /**
   * The user ID
   */
  user_id: string | null;
  /**
   * The username
   */
  username: string | null;
  /**
   * The user first name
   */
  user_first_name: string | null;
  /**
   * The user last name
   */
  user_last_name: string | null;
  /**
   * The creation date
   */
  created_at: string;
  /**
   * The attachments
   */
  attachments: Array<AttachmentResponse>;
  /**
   * The comment text
   */
  comment_text: string;
  /**
   * The comment type
   */
  comment_type: CommentType;
};
