/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ClusterHealth } from "./ClusterHealth";

/**
 * Dictionary status schema
 */
export type DictionaryStatus = {
  enabled?: boolean;
  service_health?: ClusterHealth;
  service_error?: string;
};
