/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AttachmentType } from './AttachmentType';
import type { CommentType } from './CommentType';

export type Body_submit_single_manual_field_api_v1_privacy_request__privacy_request_id__manual_field__manual_field_id__complete_post = {
  /**
   * The value for the field (optional if attachments are provided)
   */
  field_value?: (string | null);
  /**
   * Optional comment for this field
   */
  comment_text?: (string | null);
  /**
   * Comment type (required if comment_text is provided)
   */
  comment_type?: (CommentType | null);
  attachments?: Array<Blob>;
  /**
   * Attachment type (required if attachments are provided)
   */
  attachment_type?: (AttachmentType | null);
};

