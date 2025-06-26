/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentStatus } from "./ConsentStatus";

/**
 *
 */
export type ConsentStatusInfo = {
  /**
   * The message to display to the user
   */
  message: string;
  /**
   * The status of the asset
   */
  status: ConsentStatus;
};
