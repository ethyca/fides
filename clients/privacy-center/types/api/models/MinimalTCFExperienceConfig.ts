/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from "./ComponentType";
import type { MinimalTCFBannerTranslation } from "./MinimalTCFBannerTranslation";

/**
 * A minimal TCF Privacy Experience Config response, to show the smallest response body
 * needed to build the banner
 */
export type MinimalTCFExperienceConfig = {
  auto_detect_language?: boolean | null;
  component: ComponentType;
  dismissable?: boolean | null;
  translations?: Array<MinimalTCFBannerTranslation>;
};
