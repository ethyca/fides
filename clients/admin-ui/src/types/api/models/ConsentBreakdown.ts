/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AggregatedConsent } from "./AggregatedConsent";

/**
 * Response model for consent breakdown information for a given asset
 */
export type ConsentBreakdown = {
  location: string;
  page: string;
  status: AggregatedConsent;
};
