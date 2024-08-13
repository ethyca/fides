/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { MatchesEnum } from "./MatchesEnum";

/**
 * The PrivacyRule resource model.
 *
 * A list of privacy data types and what match method to use.
 */
export type PrivacyRule = {
  /**
   *
   * The MatchesEnum resource model.
   *
   * Determines how the listed resources are matched in the evaluation logic.
   *
   */
  matches: MatchesEnum;
  /**
   * A list of fides keys to be used with the matching type in a privacy rule.
   */
  values: Array<string>;
};
