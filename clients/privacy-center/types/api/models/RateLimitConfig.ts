/* istanbul ignore file */
/* tslint:disable */

import type { RateLimit } from "./RateLimit";

/**
 * A config object which allows configuring rate limits for connectors
 */
export type RateLimitConfig = {
  limits?: Array<RateLimit> | null;
  enabled?: boolean | null;
};
