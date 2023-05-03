/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from "./ComponentType";
import type { DeliveryMechanism } from "./DeliveryMechanism";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";
import type { PrivacyNoticeResponse } from "./PrivacyNoticeResponse";

/**
 * An API representation of a PrivacyExperience used for response payloads
 */
export type PrivacyExperienceResponse = {
  disabled?: boolean;
  component: ComponentType;
  delivery_mechanism: DeliveryMechanism;
  regions?: Array<PrivacyNoticeRegion>;
  component_title?: string;
  component_description?: string;
  banner_title?: string;
  banner_description?: string;
  link_label?: string;
  confirmation_button_label?: string;
  reject_button_label?: string;
  acknowledgement_button_label?: string;
  id: string;
  created_at: string;
  updated_at: string;
  version: number;
  privacy_experience_history_id: string;
  privacy_experience_template_id?: string;
  privacy_notices?: Array<PrivacyNoticeResponse>;
};
