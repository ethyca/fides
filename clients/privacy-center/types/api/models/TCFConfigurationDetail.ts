/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { TCFRestrictionType } from "./TCFRestrictionType";

/**
 * Schema for TCF Configuration detail responses
 */
export type TCFConfigurationDetail = {
  /**
   * The unique identifier of the TCF Configuration
   */
  id: string;
  /**
   * The unique name of the TCF Configuration
   */
  name: string;
  /**
   * The restriction_types defined for this configuration, grouped per purpose
   */
  restriction_types_per_purpose?: Record<string, Array<TCFRestrictionType>>;
};
