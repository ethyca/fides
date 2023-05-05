/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from "./ComponentType";
import type { DeliveryMechanism } from "./DeliveryMechanism";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";

/**
 * An API representation of a PrivacyExperience that includes an `id` field.
 * Used to help model API responses and update payloads
 */
export type PrivacyExperienceWithId = {
  disabled?: boolean;
  component: ComponentType;
  delivery_mechanism: DeliveryMechanism;
  regions: Array<PrivacyNoticeRegion>;
  component_title?: string;
  component_description?: string;
  banner_title?: string;
  banner_description?: string;
  link_label?: string;
  confirmation_button_label?: string;
  reject_button_label?: string;
  acknowledgement_button_label?: string;
  id: string;
};
