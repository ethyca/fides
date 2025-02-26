/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ServiceHealth } from "./ServiceHealth";

/**
 * Dictionary status schema
 */
export type DictionaryStatus = {
  enabled?: boolean;
  service_health?: ServiceHealth | null;
  service_error?: string | null;
};
