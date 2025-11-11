/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PreferenceFidesMetaCreate } from "./PreferenceFidesMetaCreate";

/**
 * Metadata structure for API input (user-provided fields only).
 */
export type PreferenceMetaCreate = {
  /**
   * A set of Fides-defined metadata properties for a single privacy preference.
   */
  fides?: PreferenceFidesMetaCreate | null;
};
