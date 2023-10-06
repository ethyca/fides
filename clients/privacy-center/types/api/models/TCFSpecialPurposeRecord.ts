/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { EmbeddedVendor } from "./EmbeddedVendor";
import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * Common details for non-vendor TCF sections.  Includes previously-saved preferences and
 * records where consent was previously served if applicable.
 */
export type TCFSpecialPurposeRecord = {
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
  default_preference?: UserConsentPreference;
  current_preference?: UserConsentPreference;
  outdated_preference?: UserConsentPreference;
  current_served?: boolean;
  outdated_served?: boolean;
  vendors?: Array<EmbeddedVendor>;
  systems?: Array<EmbeddedVendor>;
};
