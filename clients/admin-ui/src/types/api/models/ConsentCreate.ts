/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentMetaCreate } from "./ConsentMetaCreate";
import type { ConsentPreferenceCreate } from "./ConsentPreferenceCreate";
import type { ConsentScopeCreate } from "./ConsentScopeCreate";
import type { fidesplus__v3__schemas__identity__Identity } from "./fidesplus__v3__schemas__identity__Identity";

/**
 * Unified consent v3 schema.
 */
export type ConsentCreate = {
  identity: fidesplus__v3__schemas__identity__Identity;
  /**
   * An optional set of identifiers that are used to target the preference more specifically than just the identity. The API currently only supports the `fides.property_id` scope.
   */
  scope?: ConsentScopeCreate | null;
  /**
   * Optional metadata properties about how and where the preferences were collected. This includes information like the geographic location, method of consent, IP address, user agent, etc. The metadata can also include any custom properties that organizations choose to collect and store alongside the preferences, such as client tokens, brand or campaign identifiers, A/B test groups, etc.
   */
  meta?: ConsentMetaCreate | null;
  /**
   * A list of actual preference values chosen by the subject (e.g. 'opt-in') for the given notice (e.g. 'marketing') and experience (e.g. 'US modal'). Preferences belong to the identity and can be filtered or aggregated by the scope value.
   */
  preferences: Array<ConsentPreferenceCreate>;
};
