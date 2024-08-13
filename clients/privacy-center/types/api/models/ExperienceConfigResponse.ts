/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import { Layer1ButtonOption } from "../../index";
import type { ComponentType } from "./ComponentType";
import type { ExperienceTranslationResponse } from "./ExperienceTranslationResponse";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";
import type { PrivacyNoticeResponse } from "./PrivacyNoticeResponse";

/**
 * An API representation of ExperienceConfig used for response payloads
 */
export type ExperienceConfigResponse = {
  name?: string;
  disabled?: boolean;
  dismissable?: boolean;
  show_layer1_notices?: boolean;
  layer1_button_options?: Layer1ButtonOption;
  allow_language_selection?: boolean;
  regions: Array<PrivacyNoticeRegion>;
  id: string;
  created_at: string;
  updated_at: string;
  origin?: string;
  component: ComponentType;
  privacy_notices?: Array<PrivacyNoticeResponse>;
  translations?: Array<ExperienceTranslationResponse>;
};
