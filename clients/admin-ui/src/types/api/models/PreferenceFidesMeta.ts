/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PreferenceType } from "./PreferenceType";
import type { PropagationPolicyKey } from "./PropagationPolicyKey";

/**
 * Fides-defined metadata properties for a single preference value (includes backend-only fields).
 */
export type PreferenceFidesMeta = {
  /**
   * The type of the preference value.
   */
  preference_type?: PreferenceType;
  /**
   * The key of the policy that created the preference value, if any.
   */
  policy_key?: PropagationPolicyKey | null;
  /**
   * The Fides property id where the preference was collected
   */
  property_id?: string | null;
  /**
   * Identifier for the experience config history
   */
  experience_config_history_id?: string | null;
};
