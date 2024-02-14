/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ExperienceTranslation } from './ExperienceTranslation';
import type { PrivacyNoticeRegion } from './PrivacyNoticeRegion';

/**
 * Updating ExperienceConfig. Note that component cannot be updated once its created.
 * Translations, regions, and privacy_notice_ids must be supplied or they will be removed.
 *
 * Experience Config Updates are also re-validated with the ExperienceConfigCreate
 * schema after patch dry updates are applied.
 */
export type ExperienceConfigUpdate = {
  name?: string;
  disabled?: boolean;
  dismissable?: boolean;
  allow_language_selection?: boolean;
  regions: Array<PrivacyNoticeRegion>;
  translations: Array<ExperienceTranslation>;
  privacy_notice_ids: Array<string>;
};

