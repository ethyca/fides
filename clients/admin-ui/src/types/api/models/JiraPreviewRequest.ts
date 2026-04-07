/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Request body for the Jira ticket preview endpoint.
 *
 * All fields are optional — the endpoint falls back to saved
 * configuration from the connection's secrets.
 */
export type JiraPreviewRequest = {
  /**
   * Override summary template; falls back to saved
   */
  summary_template?: string | null;
  /**
   * Override description template; falls back to saved
   */
  description_template?: string | null;
  /**
   * Load real privacy request data; falls back to sample values
   */
  privacy_request_id?: string | null;
};
