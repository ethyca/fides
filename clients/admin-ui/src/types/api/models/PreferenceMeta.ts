/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PreferenceFidesMeta } from "./PreferenceFidesMeta";

/**
 * Metadata structure for a single preference value (includes backend-only fields).
 */
export type PreferenceMeta = {
  /**
   * A set of Fides-defined metadata properties for a single privacy preference.
   */
  fides?: PreferenceFidesMeta;
};
