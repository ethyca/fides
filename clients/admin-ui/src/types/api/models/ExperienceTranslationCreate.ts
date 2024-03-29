/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SupportedLanguage } from "./SupportedLanguage";

/**
 * Overrides ExperienceTranslation fields to make some fields required on create
 */
export type ExperienceTranslationCreate = {
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
  title: string;
  /**
   * Banner description. HTML descriptions are supported so links can be included.
   */
  banner_description?: string;
  description: string;
  /**
   * Custom link/button trigger label
   */
  trigger_link_label?: string;
};
