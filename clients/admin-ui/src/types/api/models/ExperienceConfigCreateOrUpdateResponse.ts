/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ExperienceConfigResponse } from "./ExperienceConfigResponse";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";

/**
 * Schema with the created/updated experience config with regions that succeeded or failed
 */
export type ExperienceConfigCreateOrUpdateResponse = {
  experience_config: ExperienceConfigResponse;
  linked_regions: Array<PrivacyNoticeRegion>;
  unlinked_regions: Array<PrivacyNoticeRegion>;
  skipped_regions: Array<PrivacyNoticeRegion>;
};
