/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { MonitorExecutionStatus } from "./MonitorExecutionStatus";

export type MonitorExecution = {
  id: string;
  monitor_config_id: string;
  status?: MonitorExecutionStatus | null;
  started?: string | null;
  completed?: string | null;
  classification_instances?: Array<string>;
};
