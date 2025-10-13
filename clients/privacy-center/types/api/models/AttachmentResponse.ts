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
  user_id: string | null;
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
   * The size of the attachment
   */
  retrieved_attachment_size: number | null;
  /**
   * The URL to retrieve the attachment
   */
  retrieved_attachment_url: string | null;
  /**
   * The creation date
   */
  created_at: string;
};
