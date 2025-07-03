/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CommentType } from "./CommentType";

export type Body_skip_single_manual_field_api_v1_privacy_request__privacy_request_id__connection__connection_key__manual_field_skip_post =
  {
    /**
     * The key of the field being skipped
     */
    field_key: string;
    /**
     * Required reason for skipping this field
     */
    skip_reason: string;
    /**
     * Optional additional comment
     */
    comment_text?: string | null;
    /**
     * Comment type (required if comment_text is provided)
     */
    comment_type?: CommentType | null;
  };
