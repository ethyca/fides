/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AttachmentType } from "./AttachmentType";
import type { CommentType } from "./CommentType";

export type Body_create_privacy_request_comment_api_v1_plus_privacy_request__privacy_request_id__comment_post =
  {
    comment_text: string;
    comment_type: CommentType;
    attachment_type?: AttachmentType;
    files?: Array<Blob>;
  };
