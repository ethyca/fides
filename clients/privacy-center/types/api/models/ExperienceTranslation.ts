/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SupportedLanguage } from "./SupportedLanguage";

/**
 * Experience Translation Schema
 */
export type ExperienceTranslation = {
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
   * Modal link label
   */
  modal_link_label?: string;
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
};
