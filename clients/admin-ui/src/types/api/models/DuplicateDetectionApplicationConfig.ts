/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * API model - configuration settings for duplicate privacy request detection.
 */
export type DuplicateDetectionApplicationConfig = {
  /**
   * Whether duplicate detection is enabled. Disabled by default.
   */
  enabled?: boolean | null;
  /**
   * Time window in days for duplicate detection. Default is 1 year.
   */
  time_window_days?: number | null;
  /**
   * Identity field names to match on for duplicate detection (e.g., 'email', 'phone_number'). Default is email only.
   */
  match_identity_fields?: Array<string> | null;
};
