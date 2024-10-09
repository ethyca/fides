/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { RateLimitPeriod } from "./RateLimitPeriod";

/**
 * A config object which allows configuring rate limits for connectors
 */
export type RateLimit = {
  rate: number;
  period: RateLimitPeriod;
  custom_key?: string | null;
};
