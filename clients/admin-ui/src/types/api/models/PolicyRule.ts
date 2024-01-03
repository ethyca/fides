/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PrivacyRule } from "./PrivacyRule";

/**
 * The PolicyRule resource model.
 *
 * Describes the allowed combination of the various privacy data types.
 */
export type PolicyRule = {
  name: string;
  /**
   *
   * The PrivacyRule resource model.
   *
   * A list of privacy data types and what match method to use.
   *
   */
  data_categories: PrivacyRule;
  /**
   *
   * The PrivacyRule resource model.
   *
   * A list of privacy data types and what match method to use.
   *
   */
  data_uses: PrivacyRule;
  /**
   *
   * The PrivacyRule resource model.
   *
   * A list of privacy data types and what match method to use.
   *
   */
  data_subjects: PrivacyRule;
};
