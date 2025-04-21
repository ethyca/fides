/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from "./ComponentType";
import type { Layer1ButtonOption } from "./Layer1ButtonOption";
import type { MinimalTCFBannerTranslation } from "./MinimalTCFBannerTranslation";
import type { RejectAllMechanism } from "./RejectAllMechanism";

/**
 * A minimal TCF Privacy Experience Config response, to show the smallest response body
 * needed to build the banner
 */
export type MinimalTCFExperienceConfig = {
  id: string;
  auto_detect_language?: boolean | null;
  auto_subdomain_cookie_deletion?: boolean | null;
  component: ComponentType;
  dismissable?: boolean | null;
  translations?: Array<MinimalTCFBannerTranslation>;
  /**
   * Determines the behavior of the reject all button
   */
  reject_all_mechanism?: RejectAllMechanism | null;
  /**
   * Determines the behavior of the Layer 1 button
   */
  layer1_button_options?: Layer1ButtonOption | null;
};
