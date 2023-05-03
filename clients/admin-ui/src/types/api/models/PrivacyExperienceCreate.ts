/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from "./ComponentType";
import type { DeliveryMechanism } from "./DeliveryMechanism";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";

/**
 * An API representation of a PrivacyNotice.
 * This model doesn't include an `id` so that it can be used for creation.
 * It also establishes some fields _required_ for creation
 */
export type PrivacyExperienceCreate = {
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
};
