/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from "./ComponentType";
import type { DeliveryMechanism } from "./DeliveryMechanism";
import type { ExperienceConfigResponse } from "./ExperienceConfigResponse";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";
import type { PrivacyNoticeResponseWithUserPreferences } from "./PrivacyNoticeResponseWithUserPreferences";

/**
 * An API representation of a PrivacyExperience used for response payloads
 */
export type PrivacyExperienceResponse = {
  disabled?: boolean;
  component?: ComponentType;
  delivery_mechanism?: DeliveryMechanism;
  region: PrivacyNoticeRegion;
  experience_config?: ExperienceConfigResponse;
  id: string;
  created_at: string;
  updated_at: string;
  version: number;
  privacy_experience_history_id: string;
  privacy_notices?: Array<PrivacyNoticeResponseWithUserPreferences>;
};
