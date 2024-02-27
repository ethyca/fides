/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The model defining the responsibility or role over
 * the system that processes personal data.
 *
 * Used to identify whether the organization is a
 * Controller, Processor, or Sub-Processor of the data
 */
export enum DataResponsibilityTitle {
  CONTROLLER = "Controller",
  PROCESSOR = "Processor",
  SUB_PROCESSOR = "Sub-Processor",
}
