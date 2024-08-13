/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { EmbeddedVendor } from "./EmbeddedVendor";
import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * Schema for a TCF Feature: returned in the TCF Overlay Experience
 */
export type TCFFeatureRecord = {
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
  default_preference?: UserConsentPreference;
  vendors?: Array<EmbeddedVendor>;
  systems?: Array<EmbeddedVendor>;
};
