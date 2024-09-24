/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SupportedLanguage } from "./SupportedLanguage";

/**
 * A minimal ExperienceTranslation to support building a simple TCF banner
 *
 * Minimal TCF Experiences return this single translation
 */
export type MinimalTCFBannerTranslation = {
  /**
   * Accept or confirmation button label
   */
  accept_button_label?: string | null;
  /**
   * Banner description. HTML descriptions are supported so links can be included.
   */
  banner_description?: string | null;
  /**
   * Banner title
   */
  banner_title?: string | null;
  /**
   * Overall description - used for banner as well if applicable.  HTML descriptions are supported so links can be included.
   */
  description?: string | null;
  /**
   * The language of the given translation
   */
  language: SupportedLanguage;
  /**
   * The versioned artifact of the translation and its Experience Config. Should be supplied when saving privacy preferences or notices served for additional context.
   */
  privacy_experience_config_history_id: string;
  /**
   * Privacy policy link label
   */
  privacy_policy_link_label?: string | null;
  /**
   * Privacy policy URL
   */
  privacy_policy_url?: string | null;
  /**
   * Privacy preferences link label
   */
  privacy_preferences_link_label?: string | null;
  /**
   * Purpose header for TCF banner
   */
  purpose_header?: string | null;
  /**
   * Reject button label
   */
  reject_button_label?: string | null;
  /**
   * Overall title
   */
  title?: string | null;
};
