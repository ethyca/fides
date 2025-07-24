/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { MaskingStrategyOverride } from "./MaskingStrategyOverride";

/**
 * Collection-level specific annotations used for query traversal
 */
export type CollectionMeta = {
  after?: Array<string> | null;
  erase_after?: Array<string> | null;
  skip_processing?: boolean | null;
  masking_strategy_override?: MaskingStrategyOverride | null;
  partitioning?: null;
};
