/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import { Layer1ButtonOption } from "../../index";
import type { ComponentType } from "./ComponentType";
import type { ExperienceTranslationResponse } from "./ExperienceTranslationResponse";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";
import type { SupportedLanguage } from "./SupportedLanguage";

/**
 * Schema for embedding an Experience Config in a Privacy Experience response.
 *
 * - Privacy Notices aren't displayed here; they are instead going to be top-level.
 *
 * - Additionally, ExperienceTranslation fields are temporarily top-level for backwards compatibility
 */
export type ExperienceConfigResponseNoNotices = {
  language: SupportedLanguage;
  /**
   * Accept or confirmation button label
   */
  accept_button_label?: string;
  /**
   * Acknowledge button label for notice only
   */
  acknowledge_button_label?: string;
  /**
   * Banner title
   */
  banner_title?: string;
  /**
   * Whether the given translation is the default
   */
  is_default?: boolean;
  /**
   * Privacy policy link label
   */
  privacy_policy_link_label?: string;
  /**
   * Privacy policy URL
   */
  privacy_policy_url?: string;
  /**
   * Privacy preferences link label
   */
  privacy_preferences_link_label?: string;
  /**
   * Reject button label
   */
  reject_button_label?: string;
  /**
   * Save button label
   */
  save_button_label?: string;
  /**
   * Overall title
   */
  title?: string;
  /**
   * Banner description. HTML descriptions are supported so links can be included.
   */
  banner_description?: string;
  /**
   * Overall description - used for banner as well if applicable.  HTML descriptions are supported so links can be included.
   */
  description?: string;
  modal_link_label?: string;
  name?: string;
  disabled?: boolean;
  dismissable?: boolean;
  show_layer1_notices?: boolean;
  layer1_button_options?: Layer1ButtonOption;
  allow_language_selection?: boolean;
  regions: Array<PrivacyNoticeRegion>;
  id: string;
  created_at: string;
  updated_at: string;
  component: ComponentType;
  translations: Array<ExperienceTranslationResponse>;
};
