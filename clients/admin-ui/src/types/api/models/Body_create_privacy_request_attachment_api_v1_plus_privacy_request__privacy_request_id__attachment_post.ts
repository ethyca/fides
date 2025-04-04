/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AttachmentType } from "./AttachmentType";

export type Body_create_privacy_request_attachment_api_v1_plus_privacy_request__privacy_request_id__attachment_post =
  {
    /**
     * The ID of the user uploading the file. Example:'fid_12345'
     */
    user_id: string;
    /**
     * The type of the attachment. Example: 'internal_use_only'
     */
    attachment_type: AttachmentType;
    /**
     * The storage config key. Example: 'local_storage_config'
     */
    storage_key: string;
    attachment_file: Blob;
  };
