/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentStatus } from "./ConsentStatus";

/**
 * Response model for consent breakdown information for a given asset
 */
export type ConsentBreakdown = {
  location: string;
  page: string;
  status: ConsentStatus;
};
