/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from './ComponentType';
import type { ExperienceTranslationCreate } from './ExperienceTranslationCreate';
import type { PrivacyNoticeRegion } from './PrivacyNoticeRegion';

/**
 * Schema for creating Experience Configs via the API
 */
export type ExperienceConfigCreate = {
  name?: string;
  disabled?: boolean;
  dismissable?: boolean;
  allow_language_selection?: boolean;
  regions?: Array<PrivacyNoticeRegion>;
  translations?: Array<ExperienceTranslationCreate>;
  component: ComponentType;
  privacy_notice_ids?: Array<string>;
};

