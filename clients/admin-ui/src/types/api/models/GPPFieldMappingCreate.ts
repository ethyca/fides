/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { GPPMechanismMapping } from "./GPPMechanismMapping";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";

export type GPPFieldMappingCreate = {
  region: PrivacyNoticeRegion;
  notice?: Array<string> | null;
  mechanism?: Array<GPPMechanismMapping> | null;
};
