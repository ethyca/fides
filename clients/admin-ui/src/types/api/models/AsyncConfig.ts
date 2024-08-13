/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AsyncStrategy } from "./AsyncStrategy";

/**
 * Async config only has strategy for now, but could be
 * extended with other configuration options when we add polling
 */
export type AsyncConfig = {
  strategy: AsyncStrategy;
};
