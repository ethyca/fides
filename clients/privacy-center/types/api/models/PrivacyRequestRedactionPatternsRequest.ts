/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Request schema for updating privacy request redaction patterns.
 */
export type PrivacyRequestRedactionPatternsRequest = {
  /**
   * List of regex patterns used to redact dataset, collection, and field names in privacy request package reports
   */
  patterns: Array<string>;
};
