/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PreferenceSource } from "./PreferenceSource";

/**
 * Fides-defined metadata properties for a single preference value (includes backend-only fields).
 */
export type PreferenceFidesMeta = {
  /**
   * ISO timestamp when the preference was collected (auto-populated if not provided)
   */
  collected_at?: string | null;
  /**
   * Whether the preference value was created from a parent or child preference with override_mode
   */
  override?: boolean | null;
  /**
   * Whether the preference value was derived from a parent preference rather than being explicitly saved.
   */
  derived?: boolean | null;
  /**
   * The source of the preference value.
   */
  source?: PreferenceSource | null;
};
