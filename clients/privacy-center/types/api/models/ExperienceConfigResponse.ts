/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from "./ComponentType";
import type { DeliveryMechanism } from "./DeliveryMechanism";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";

/**
 * An API representation of ExperienceConfig used for response payloads
 */
export type ExperienceConfigResponse = {
  acknowledgement_button_label?: string;
  banner_title?: string;
  banner_description?: string;
  component?: ComponentType;
  component_title?: string;
  component_description?: string;
  confirmation_button_label?: string;
  delivery_mechanism?: DeliveryMechanism;
  disabled?: boolean;
  is_default?: boolean;
  link_label?: string;
  reject_button_label?: string;
  id: string;
  experience_config_history_id: string;
  version: number;
  created_at: string;
  updated_at: string;
  regions: Array<PrivacyNoticeRegion>;
};
