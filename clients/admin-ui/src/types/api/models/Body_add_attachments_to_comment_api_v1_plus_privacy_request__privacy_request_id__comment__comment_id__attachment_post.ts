/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AttachmentType } from "./AttachmentType";

export type Body_add_attachments_to_comment_api_v1_plus_privacy_request__privacy_request_id__comment__comment_id__attachment_post =
  {
    attachment_type: AttachmentType;
    files?: Array<Blob>;
  };
