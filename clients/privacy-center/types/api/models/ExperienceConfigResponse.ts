/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from "./ComponentType";
import type { ExperienceConfigTranslation } from "./ExperienceConfigTranslation";

/**
 * An API representation of ExperienceConfig used for response payloads
 */
export type ExperienceConfigResponse = {
  translations: Array<ExperienceConfigTranslation>;
  dismissable?: boolean;
  allow_language_selection?: boolean;
  custom_asset_id?: string;
  id: string;
  component: ComponentType;
  created_at: string;
  updated_at: string;
};
