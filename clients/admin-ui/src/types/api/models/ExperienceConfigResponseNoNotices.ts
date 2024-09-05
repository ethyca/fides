/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from "./ComponentType";
import type { ExperienceTranslationResponse } from "./ExperienceTranslationResponse";
import type { Layer1ButtonOption } from "./Layer1ButtonOption";
import type { MinimalProperty } from "./MinimalProperty";
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
  accept_button_label?: string | null;
  /**
   * Acknowledge button label for notice only
   */
  acknowledge_button_label?: string | null;
  /**
   * Banner title
   */
  banner_title?: string | null;
  /**
   * Whether the given translation is the default
   */
  is_default?: boolean | null;
  /**
   * Privacy policy link label
   */
  privacy_policy_link_label?: string | null;
  /**
   * Modal link label
   */
  modal_link_label?: string | null;
  /**
   * Privacy policy URL
   */
  privacy_policy_url?: string | null;
  /**
   * Privacy preferences link label
   */
  privacy_preferences_link_label?: string | null;
  /**
   * Reject button label
   */
  reject_button_label?: string | null;
  /**
   * Save button label
   */
  save_button_label?: string | null;
  /**
   * Overall title
   */
  title?: string | null;
  /**
   * Banner description. HTML descriptions are supported so links can be included if allowHTMLDescription option is true.
   */
  banner_description?: string | null;
  /**
   * Overall description - used for banner as well if applicable.  HTML descriptions are supported so links can be included.
   */
  description?: string | null;
  /**
   * Purpose header appears above the list of purposes in the TCF overlay
   */
  purpose_header?: string | null;
  name: string;
  disabled?: boolean | null;
  dismissable?: boolean | null;
  show_layer1_notices?: boolean | null;
  layer1_button_options?: Layer1ButtonOption | null;
  allow_language_selection?: boolean | null;
  auto_detect_language?: boolean | null;
  regions: Array<PrivacyNoticeRegion>;
  id: string;
  created_at: string;
  updated_at: string;
  component: ComponentType;
  translations?: Array<ExperienceTranslationResponse>;
  properties?: Array<MinimalProperty>;
};
