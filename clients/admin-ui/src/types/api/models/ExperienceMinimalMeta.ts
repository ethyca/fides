/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * A subset of the Experience Meta information for use in the minimal TCF banner
 */
export type ExperienceMinimalMeta = {
  /**
   * A hashed value that can be compared to previously-fetched hash values to determine if the Experience has meaningfully changed
   */
  version_hash?: string | null;
};
