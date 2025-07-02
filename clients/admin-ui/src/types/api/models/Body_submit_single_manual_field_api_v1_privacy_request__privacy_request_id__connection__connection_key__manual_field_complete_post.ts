/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AttachmentType } from "./AttachmentType";
import type { CommentType } from "./CommentType";

export type Body_submit_single_manual_field_api_v1_privacy_request__privacy_request_id__connection__connection_key__manual_field_complete_post =
  {
    /**
     * The key of the field being submitted
     */
    field_key: string;
    /**
     * The value for the field (optional if attachment is provided)
     */
    field_value?: string | null;
    /**
     * Optional comment for this field
     */
    comment_text?: string | null;
    /**
     * Comment type (required if comment_text is provided)
     */
    comment_type?: CommentType | null;
    /**
     * Optional file attachment
     */
    attachment?: Blob | null;
    /**
     * Attachment type (required if attachment is provided)
     */
    attachment_type?: AttachmentType | null;
  };
