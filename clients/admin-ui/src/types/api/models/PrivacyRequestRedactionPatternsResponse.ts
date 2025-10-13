/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response schema for privacy request redaction patterns.
 */
export type PrivacyRequestRedactionPatternsResponse = {
  /**
   * List of regex patterns used to redact dataset, collection, and field names in privacy request package reports
   */
  patterns: Array<string>;
};

