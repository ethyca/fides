/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from "./ComponentType";
import type { ExperienceTranslationResponse } from "./ExperienceTranslationResponse";
import type { Layer1ButtonOption } from "./Layer1ButtonOption";
import type { MinimalProperty } from "./MinimalProperty";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";
import type { RejectAllMechanism } from "./RejectAllMechanism";

/**
 * Schema for embedding an Experience Config in a Privacy Experience response.
 *
 * - Privacy Notices aren't displayed here; they are instead going to be top-level.
 */
export type ExperienceConfigResponseNoNotices = {
  name: string;
  disabled?: boolean | null;
  dismissable?: boolean | null;
  show_layer1_notices?: boolean | null;
  layer1_button_options?: Layer1ButtonOption | null;
  allow_language_selection?: boolean | null;
  auto_detect_language?: boolean | null;
  auto_subdomain_cookie_deletion?: boolean | null;
  allow_vendor_asset_disclosure?: boolean | null;
  asset_disclosure_include_types?: Array<string> | null;
  regions: Array<PrivacyNoticeRegion>;
  tcf_configuration_id?: string | null;
  id: string;
  created_at: string;
  updated_at: string;
  component: ComponentType;
  translations?: Array<ExperienceTranslationResponse>;
  properties?: Array<MinimalProperty>;
  /**
   * Determines the behavior of the reject all button
   */
  reject_all_mechanism?: RejectAllMechanism | null;
};
