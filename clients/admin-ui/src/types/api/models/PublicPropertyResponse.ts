/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { MinimalMessagingTemplate } from "./MinimalMessagingTemplate";
import type { MinimalPrivacyExperienceConfig } from "./MinimalPrivacyExperienceConfig";
import type { PrivacyCenterConfig } from "./PrivacyCenterConfig";
import type { PropertyType } from "./PropertyType";

/**
 * Schema that represents a `Property` as returned in the
 * public-facing Property APIs.
 *
 * NOTE: Add to this schema with care. Any fields added to
 * this response schema will be exposed in public-facing
 * (i.e. unauthenticated) API responses. If a field has
 * sensitive information, it should NOT be added to this schema!
 *
 * Any `Property` fields that are sensitive should be added to the
 * appropriate non-public schemas that extend this schema.
 */
export type PublicPropertyResponse = {
  name: string;
  type: PropertyType;
  id?: string | null;
  experiences: Array<MinimalPrivacyExperienceConfig>;
  messaging_templates?: Array<MinimalMessagingTemplate> | null;
  privacy_center_config?: PrivacyCenterConfig | null;
  stylesheet?: string | null;
  paths: Array<string>;
};
