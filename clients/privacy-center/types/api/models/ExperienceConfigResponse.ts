/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from "./ComponentType";
import type { EmbeddedPrivacyNoticeResponse } from "./EmbeddedPrivacyNoticeResponse";
import type { ExperienceTranslationResponse } from "./ExperienceTranslationResponse";
import type { Layer1ButtonOption } from "./Layer1ButtonOption";
import type { MinimalProperty } from "./MinimalProperty";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";

/**
 * An API representation of ExperienceConfig used for response payloads
 */
export type ExperienceConfigResponse = {
  name: string;
  disabled?: boolean | null;
  dismissable?: boolean | null;
  show_layer1_notices?: boolean | null;
  layer1_button_options?: Layer1ButtonOption | null;
  allow_language_selection?: boolean | null;
  auto_detect_language?: boolean | null;
  regions: Array<PrivacyNoticeRegion>;
  id: string;
  created_at: string;
  updated_at: string;
  origin?: string | null;
  component: ComponentType;
  privacy_notices?: Array<EmbeddedPrivacyNoticeResponse>;
  translations?: Array<ExperienceTranslationResponse>;
  properties?: Array<MinimalProperty>;
};
