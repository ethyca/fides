/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SupportedLanguage } from './SupportedLanguage';

/**
 * Adds the historical id to the translation for the response
 */
export type ExperienceTranslationResponse = {
  language: SupportedLanguage;
  /**
   * Overlay 'Accept button displayed on the Banner and Privacy Preferences' or Privacy Center 'Confirmation button label'
   */
  accept_button_label?: string;
  /**
   * Overlay 'Acknowledge button label for notice only banner'
   */
  acknowledge_button_label?: string;
  /**
   * Overlay 'Banner Description'
   */
  banner_description?: string;
  /**
   * Overlay 'Banner title'
   */
  banner_title?: string;
  /**
   * Overlay 'Description' or Privacy Center 'Description'
   */
  description?: string;
  /**
   * Whether the given translation is the default
   */
  is_default?: boolean;
  /**
   * Overlay and Privacy Center 'Privacy policy link label'
   */
  privacy_policy_link_label?: string;
  /**
   * Overlay and Privacy Center 'Privacy policy URL
   */
  privacy_policy_url?: string;
  /**
   * Overlay 'Privacy preferences link label'
   */
  privacy_preferences_link_label?: string;
  /**
   * Overlay 'Reject button displayed on the Banner and 'Privacy Preferences' of Privacy Center 'Reject button label'
   */
  reject_button_label?: string;
  /**
   * Overlay 'Privacy preferences 'Save' button label
   */
  save_button_label?: string;
  /**
   * Overlay 'title' or Privacy Center 'title'
   */
  title?: string;
  experience_config_history_id: string;
};

