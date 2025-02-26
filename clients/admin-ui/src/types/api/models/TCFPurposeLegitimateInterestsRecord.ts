/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { EmbeddedVendor } from "./EmbeddedVendor";
import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * Schema for a TCF Purpose with Legitimate Interests Legal Basis returned in the TCF Overlay Experience
 */
export type TCFPurposeLegitimateInterestsRecord = {
  /**
   * Official GVL purpose ID. Used for linking with other records, e.g. vendors, cookies, etc.
   */
  id: number;
  /**
   * Name of the GVL purpose.
   */
  name: string;
  /**
   * Description of the GVL purpose.
   */
  description: string;
  /**
   * Illustrative examples of the purpose.
   */
  illustrations: Array<string>;
  /**
   * The fideslang default taxonomy data uses that are associated with the purpose.
   */
  data_uses: Array<string>;
  default_preference?: UserConsentPreference | null;
  vendors?: Array<EmbeddedVendor>;
  systems?: Array<EmbeddedVendor>;
};
