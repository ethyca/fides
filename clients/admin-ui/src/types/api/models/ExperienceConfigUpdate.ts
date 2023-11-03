/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { BannerEnabled } from "./BannerEnabled";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";

/**
 * Updating ExperienceConfig. Note that component cannot be updated once its created
 */
export type ExperienceConfigUpdate = {
  /**
   * Overlay 'Accept button displayed on the Banner and Privacy Preferences' or Privacy Center 'Confirmation button label'
   */
  accept_button_label?: string;
  /**
   * Overlay 'Acknowledge button label for notice only banner'
   */
  acknowledge_button_label?: string;
  /**
   * Overlay 'Banner'
   */
  banner_enabled?: BannerEnabled;
  /**
   * Overlay 'Banner Description' or Privacy Center 'Description'
   */
  description?: string;
  /**
   * Whether the given ExperienceConfig is disabled
   */
  disabled?: boolean;
  /**
   * Whether the given ExperienceConfig is a global default
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
   * Regions using this ExperienceConfig
   */
  regions?: Array<PrivacyNoticeRegion>;
  /**
   * Overlay 'Reject button displayed on the Banner and 'Privacy Preferences' of Privacy Center 'Reject button label'
   */
  reject_button_label?: string;
  /**
   * Overlay 'Privacy preferences 'Save' button label
   */
  save_button_label?: string;
  /**
   * Overlay 'Banner title' or Privacy Center 'title'
   */
  title?: string;
};
