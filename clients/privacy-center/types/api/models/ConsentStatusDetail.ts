/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentStatus } from "./ConsentStatus";
import type { ConsentStatusReason } from "./ConsentStatusReason";

/**
 * Model for storing consent_status_details for a given asset
 */
export type ConsentStatusDetail = {
  /**
   * The consent status for the given page and location
   */
  consent_status: ConsentStatus;
  /**
   * The relevant reasons for the consent status
   */
  consent_status_reason?: ConsentStatusReason | null;
};
