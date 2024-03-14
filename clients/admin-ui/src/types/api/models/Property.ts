/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import { MinimalPrivacyExperience } from "./MinimalPrivacyExperience";
import { PropertyType } from "./PropertyType";

export type Property = {
  id?: string;
  name: string;
  type: PropertyType;
  experiences: Array<MinimalPrivacyExperience>;
};
