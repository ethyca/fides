/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Features that can be enabled for different integration types.
 * These control which tabs and functionality are available in the integration detail view.
 */
export enum IntegrationFeature {
  DATA_DISCOVERY = "DATA_DISCOVERY",
  DATA_SYNC = "DATA_SYNC",
  TASKS = "TASKS",
  WITHOUT_CONNECTION = "WITHOUT_CONNECTION",
  DSR_AUTOMATION = "DSR_AUTOMATION",
  CONDITIONS = "CONDITIONS",
}
