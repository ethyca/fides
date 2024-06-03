/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ClassifyParams } from "./ClassifyParams";

/**
 * Base model for monitor config
 */
export type MonitorConfig = {
  name: string;
  key?: string;
  connection_config_key: string;
  classify_params: ClassifyParams;
};
