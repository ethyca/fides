/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { BannerEnabled } from "./BannerEnabled";
import type { ComponentType } from "./ComponentType";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";

/**
 * An API representation to create ExperienceConfig.
 * This model doesn't include an `id` so that it can be used for creation.
 * It also establishes some fields _required_ for creation
 */
export type ExperienceConfigCreate = {
  accept_button_label: string;
  /**
   * Overlay 'Acknowledge button label for notice only banner'
   */
  acknowledge_button_label?: string;
  banner_description?: string | null;
  /**
   * Overlay 'Banner'
   */
  banner_enabled?: BannerEnabled;
  banner_title?: string | null;
  description: string;
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
  privacy_policy_link_label?: string | null;
  /**
   * Overlay and Privacy Center 'Privacy policy URL
   */
  privacy_policy_url?: string | null;
  /**
   * Overlay 'Privacy preferences link label'
   */
  privacy_preferences_link_label?: string;
  /**
   * Regions using this ExperienceConfig
   */
  regions?: Array<PrivacyNoticeRegion>;
  reject_button_label: string;
  save_button_label: string;
  title: string;
  component: ComponentType;
};
