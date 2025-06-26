/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * API model that represents consent information for a web monitor staged resource
 */
export type ConsentInfo = {
  /**
   * Pages where the asset was found with default consent, indexed by location
   */
  default?: Record<string, Array<string>>;
  /**
   * Pages where the asset was found without consent, indexed by location
   */
  denied?: Record<string, Array<string>>;
  /**
   * Pages where the asset was found with consent, indexed by location
   */
  granted?: Record<string, Array<string>>;
};
