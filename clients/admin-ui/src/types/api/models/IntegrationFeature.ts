/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Features that can be enabled for different integration types.
 * These control which tabs and functionality are available in the integration detail view.
 */
export enum IntegrationFeature {
  DATA_DISCOVERY = "data_discovery",
  DATA_SYNC = "data_sync",
  TASKS = "tasks",
  WITHOUT_CONNECTION = "without_connection",
  DSR_AUTOMATION = "dsr_automation",
}
