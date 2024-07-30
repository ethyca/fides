/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import { Layer1ButtonOption } from "~/features/privacy-experience/form/constants";
import type { ComponentType } from "./ComponentType";
import type { ExperienceTranslationCreate } from "./ExperienceTranslationCreate";
import type { MinimalProperty } from "./MinimalProperty";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";

/**
 * Schema for creating Experience Configs via the API
 *
 * Privacy notices are specified as a list of ids instead of keys like the template
 */
export type ExperienceConfigCreate = {
  name: string;
  disabled?: boolean;
  dismissable?: boolean;
  show_layer1_notices?: boolean;
  layer1_button_options?: Layer1ButtonOption;
  allow_language_selection?: boolean;
  auto_detect_language?: boolean;
  regions?: Array<PrivacyNoticeRegion>;
  component: ComponentType;
  privacy_notice_ids?: Array<string>;
  translations?: Array<ExperienceTranslationCreate>;
  properties?: Array<MinimalProperty>;
};
