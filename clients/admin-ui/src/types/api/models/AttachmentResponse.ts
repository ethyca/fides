/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Schema and helper functionality for AttachmentResponse objects stored in the AttachmentResponse table.
 */
export type AttachmentResponse = {
  /**
   * The attachment ID
   */
  id: string;
  /**
   * The user ID
   */
  user_id: string;
  /**
   * The user name
   */
  username: string;
  /**
   * The user first name
   */
  user_first_name: string | null;
  /**
   * The user last name
   */
  user_last_name: string | null;
  /**
   * The attachment name
   */
  file_name: string;
  /**
   * The attachment type
   */
  attachment_type: string;
  /**
   * For files <= 5mb, contains the body of the file. And the URL to retrieve the attachmentFor larger files containes the URL to retrieve the attachment
   */
  retrieved_attachment: Blob | string;
  /**
   * The URL to download the attachment
   */
  download_url: string;
  /**
   * The creation date
   */
  created_at: string;
};
