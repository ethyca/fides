/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { EmbeddedVendor } from "./EmbeddedVendor";
import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * Schema for a TCF Feature or a special feature: returned in the TCF Overlay Experience
 */
export type TCFFeatureRecord = {
  default_preference?: UserConsentPreference;
  current_preference?: UserConsentPreference;
  outdated_preference?: UserConsentPreference;
  current_served?: boolean;
  outdated_served?: boolean;
  /**
   * Official GVL feature ID or special feature ID
   */
  id: number;
  /**
   * Name of the GVL feature or special feature.
   */
  name: string;
  /**
   * Description of the GVL feature or special feature.
   */
  description: string;
  vendors?: Array<EmbeddedVendor>;
  systems?: Array<EmbeddedVendor>;
};
