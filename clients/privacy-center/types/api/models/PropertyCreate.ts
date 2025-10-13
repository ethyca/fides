/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { fides__api__schemas__privacy_center_config__PrivacyCenterConfig } from "./fides__api__schemas__privacy_center_config__PrivacyCenterConfig";
import type { MinimalPrivacyExperienceConfig } from "./MinimalPrivacyExperienceConfig";
import type { PropertyType } from "./PropertyType";

export type PropertyCreate = {
  name: string;
  type: PropertyType;
  id?: string | null;
  experiences: Array<MinimalPrivacyExperienceConfig>;
  privacy_center_config?: fides__api__schemas__privacy_center_config__PrivacyCenterConfig | null;
  stylesheet?: string | null;
  paths: Array<string>;
};
