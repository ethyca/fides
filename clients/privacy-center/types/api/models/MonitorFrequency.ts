/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Enum representing monitor frequency. Not used in DB but needed for translating to API schema
 */
export enum MonitorFrequency {
  DAILY = "Daily",
  WEEKLY = "Weekly",
  MONTHLY = "Monthly",
  NOT_SCHEDULED = "Not scheduled",
}
