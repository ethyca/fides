/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from "./ComponentType";
import type { ExperienceMeta } from "./ExperienceMeta";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";

/**
 * Privacy Experience Response only containing region, component, id, and meta information
 */
export type PrivacyExperienceMetaResponse = {
  id: string;
  region: PrivacyNoticeRegion;
  component?: ComponentType | null;
  meta?: ExperienceMeta | null;
  /**
   * The number of vendors in the TCF experience. Only populated for TCF experiences.
   */
  vendor_count?: number | null;
};
