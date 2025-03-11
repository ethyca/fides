/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { MinimalPrivacyExperienceConfig } from "./MinimalPrivacyExperienceConfig";
import type { PrivacyCenterConfig } from "./PrivacyCenterConfig";
import type { PropertyType } from "./PropertyType";

export type PropertyCreate = {
  name: string;
  type: PropertyType;
  id?: string | null;
  experiences: Array<MinimalPrivacyExperienceConfig>;
  privacy_center_config?: PrivacyCenterConfig | null;
  stylesheet?: string | null;
  paths: Array<string>;
};
