/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from "./ComponentType";
import { MinimalProperty } from "./MinimalProperty";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";

/**
 * Limited schema that supplies the minimum details for the Experience Config list view
 */
export type ExperienceConfigListViewResponse = {
  id: string;
  name?: string;
  regions: Array<PrivacyNoticeRegion>;
  properties: Array<MinimalProperty>;
  component: ComponentType;
  updated_at: string;
  disabled: boolean;
};
