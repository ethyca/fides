/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from "./ComponentType";
import type { ExperienceTranslationResponse } from "./ExperienceTranslationResponse";
import type { MinimalProperty } from "./MinimalProperty";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";
import type { PrivacyNoticeResponse } from "./PrivacyNoticeResponse";

/**
 * An API representation of ExperienceConfig used for response payloads
 */
export type ExperienceConfigResponse = {
  name: string;
  disabled?: boolean;
  dismissable?: boolean;
  allow_language_selection?: boolean;
  auto_detect_language?: boolean;
  regions: Array<PrivacyNoticeRegion>;
  id: string;
  created_at: string;
  updated_at: string;
  origin?: string;
  component: ComponentType;
  privacy_notices?: Array<PrivacyNoticeResponse>;
  translations?: Array<ExperienceTranslationResponse>;
  properties?: Array<MinimalProperty>;
};
