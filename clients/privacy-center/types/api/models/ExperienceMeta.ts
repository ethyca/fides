/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { TCMobileData } from './TCMobileData';

/**
 * Supplements experience with developer-friendly meta information
 */
export type ExperienceMeta = {
  /**
   * A hashed value that can be compared to previously-fetched hash values to determine if the Experience has meaningfully changed
   */
  version_hash?: string;
  /**
   * The fides string (TC String + AC String) corresponding to a user opting in to all available options
   */
  accept_all_fides_string?: string;
  accept_all_fides_mobile_data?: TCMobileData;
  /**
   * The fides string (TC String + AC String) corresponding to a user opting out of all available options
   */
  reject_all_fides_string?: string;
  reject_all_fides_mobile_data?: TCMobileData;
};

