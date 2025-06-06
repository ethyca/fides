/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from "./ComponentType";
import type { ExperienceTranslationCreate } from "./ExperienceTranslationCreate";
import type { Layer1ButtonOption } from "./Layer1ButtonOption";
import type { MinimalProperty } from "./MinimalProperty";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";
import type { RejectAllMechanism } from "./RejectAllMechanism";

/**
 * Schema for creating Experience Configs via the API
 *
 * Privacy notices are specified as a list of ids instead of keys like the template
 */
export type ExperienceConfigCreate = {
  name: string;
  disabled?: boolean | null;
  dismissable?: boolean | null;
  show_layer1_notices?: boolean | null;
  layer1_button_options?: Layer1ButtonOption | null;
  allow_language_selection?: boolean | null;
  auto_detect_language?: boolean | null;
  auto_subdomain_cookie_deletion?: boolean | null;
  regions?: Array<PrivacyNoticeRegion>;
  tcf_configuration_id?: string | null;
  component: ComponentType;
  /**
   * Determines the behavior of the reject all button
   */
  reject_all_mechanism?: RejectAllMechanism | null;
  privacy_notice_ids?: Array<string>;
  translations?: Array<ExperienceTranslationCreate>;
  properties?: Array<MinimalProperty>;
};
