/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SupportedLanguage } from "./SupportedLanguage";

/**
 * Adds the historical id to the translation for the response
 */
export type ExperienceTranslationResponse = {
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
   * Overall description - used for banner as well if applicable.  HTML descriptions are supported so links can be included if allowHTMLDescription option is true.
   */
  description?: string | null;
  /**
   * The versioned artifact of the translation and its Experience Config. Should be supplied when saving privacy preferences for additional context.
   */
  privacy_experience_config_history_id: string;
  /**
   * Purpose header appears above the list of purposes in the TCF overlay
   */
  purpose_header?: string | null;
};
