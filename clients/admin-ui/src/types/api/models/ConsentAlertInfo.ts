/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AlertLevel } from "./AlertLevel";

/**
 * Used to summarize consent status information for a group of staged resources.
 */
export type ConsentAlertInfo = {
  /**
   * The message to display to the user
   */
  message: string;
  /**
   * The status of the asset
   */
  status: AlertLevel;
};
