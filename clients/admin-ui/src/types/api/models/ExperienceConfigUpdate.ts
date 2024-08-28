/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ExperienceTranslation } from "./ExperienceTranslation";
import type { Layer1ButtonOption } from "./Layer1ButtonOption";
import type { MinimalProperty } from "./MinimalProperty";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";

/**
 * The schema to update an ExperienceConfig via the API.
 *
 * Note that component cannot be updated once its created.
 * Translations, regions, and privacy_notice_ids must be supplied or they will be removed.  They are
 * required in the request to hopefully make their removal intentional.
 *
 * Experience Config Updates are also re-validated with the ExperienceConfigCreate
 * schema after patch dry updates are applied.
 */
export type ExperienceConfigUpdate = {
  name?: string | null;
  disabled?: boolean | null;
  dismissable?: boolean | null;
  show_layer1_notices?: boolean | null;
  layer1_button_options?: Layer1ButtonOption | null;
  allow_language_selection?: boolean | null;
  auto_detect_language?: boolean | null;
  regions: Array<PrivacyNoticeRegion>;
  translations: Array<ExperienceTranslation>;
  privacy_notice_ids: Array<string>;
  properties: Array<MinimalProperty>;
};
