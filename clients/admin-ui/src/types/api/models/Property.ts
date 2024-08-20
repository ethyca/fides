/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { MinimalMessagingTemplate } from "./MinimalMessagingTemplate";
import type { MinimalPrivacyExperienceConfig } from "./MinimalPrivacyExperienceConfig";
import type { PrivacyCenterConfig } from "./PrivacyCenterConfig";
import type { PropertyType } from "./PropertyType";

/**
 * A schema representing the complete `Property` model.
 *
 * This schema extends the base `PublicPropertyResponse` schema,
 * which only includes fields that are appropriate to be exposed
 * in public endpoints.
 *
 * Any `Property` fields that are sensitive but need to be included in private
 * API responses should be added to this schema.
 */
export type Property = {
  name: string;
  type: PropertyType;
  id?: string | null;
  experiences: Array<MinimalPrivacyExperienceConfig>;
  messaging_templates?: Array<MinimalMessagingTemplate> | null;
  privacy_center_config?: PrivacyCenterConfig | null;
  stylesheet?: string | null;
  paths: Array<string>;
};
