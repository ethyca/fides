/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { GPPMechanismMapping } from "./GPPMechanismMapping";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type GPPFieldMappingCreate = {
  region: PrivacyNoticeRegion;
  notice?: Array<string>;
  mechanism?: Array<GPPMechanismMapping>;
};
