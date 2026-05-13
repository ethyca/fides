/* istanbul ignore file */
/* tslint:disable */

import type { MaskingStrategyConfigurationDescription } from "./MaskingStrategyConfigurationDescription";

/**
 * The description model for a masking strategy
 */
export type MaskingStrategyDescription = {
  name: string;
  description: string;
  configurations: Array<MaskingStrategyConfigurationDescription>;
};
