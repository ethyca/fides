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
   * Pages where the asset was found with denied consent, indexed by location
   */
  denied?: Record<string, Array<string>>;
  /**
   * Pages where the asset was found with consent, indexed by location
   */
  granted?: Record<string, Array<string>>;
  /**
   * Pages where the asset was loaded and a CMP error was detected, indexed by location
   */
  cmp_error?: Record<string, Array<string>>;
};
