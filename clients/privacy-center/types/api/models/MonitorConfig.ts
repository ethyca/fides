/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ClassifyParams } from "./ClassifyParams";
import type { MonitorFrequency } from "./MonitorFrequency";

/**
 * Base model for monitor config
 */
export type MonitorConfig = {
  name: string;
  key?: string;
  connection_config_key: string;
  classify_params: ClassifyParams;
  /**
   * The databases that the monitor is scoped to actively monitor
   */
  databases?: Array<string>;
  execution_start_date?: string;
  execution_frequency?: MonitorFrequency;
};
