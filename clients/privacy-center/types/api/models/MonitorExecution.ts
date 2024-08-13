/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { MonitorExecutionStatus } from "./MonitorExecutionStatus";

export type MonitorExecution = {
  id: string;
  monitor_config_id: string;
  status?: MonitorExecutionStatus;
  started?: string;
  completed?: string;
  classification_instances?: Array<string>;
};
