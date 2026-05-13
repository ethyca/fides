/* istanbul ignore file */
/* tslint:disable */

import type { TCMobileData } from "./TCMobileData";

/**
 * Decode response schema for returning TC Mobile Data
 */
export type TCDecode = {
  fides_mobile_data?: TCMobileData | null;
};
