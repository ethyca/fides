/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from "./ComponentType";
import type { DeliveryMechanism } from "./DeliveryMechanism";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";

/**
 * An API representation to create ExperienceConfig.
 * This model doesn't include an `id` so that it can be used for creation.
 * It also establishes some fields _required_ for creation
 */
export type ExperienceConfigCreate = {
  acknowledgement_button_label?: string;
  banner_title?: string;
  banner_description?: string;
  component: ComponentType;
  component_title: string;
  component_description?: string;
  confirmation_button_label?: string;
  delivery_mechanism: DeliveryMechanism;
  disabled?: boolean;
  is_default?: boolean;
  link_label?: string;
  reject_button_label?: string;
  regions: Array<PrivacyNoticeRegion>;
};
