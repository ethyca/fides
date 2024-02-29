/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from "./ComponentType";
import type { ExperienceTranslationCreate } from "./ExperienceTranslationCreate";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";

/**
 * Schema for creating Experience Configs via the API
 *
 * Privacy notices are specified as a list of ids instead of keys like the template
 */
export type ExperienceConfigCreate = {
  name?: string;
  disabled?: boolean;
  dismissable?: boolean;
  allow_language_selection?: boolean;
  regions?: Array<PrivacyNoticeRegion>;
  component: ComponentType;
  privacy_notice_ids?: Array<string>;
  translations?: Array<ExperienceTranslationCreate>;
};
