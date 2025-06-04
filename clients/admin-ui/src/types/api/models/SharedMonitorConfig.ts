/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { MinimalClassifyParams } from "./MinimalClassifyParams";

/**
 * Model for shareable monitor configurations that can be reused across monitors.
 * Initially only sharing regex patterns, but extensible for future fields.
 */
export type SharedMonitorConfig = {
  id?: string | null;
  /**
   * The name of the shared monitor config.
   */
  name: string;
  /**
   * Optional key of the shared monitor config. If a key is not provided, one will be generated from the name.
   */
  key?: string | null;
  /**
   * A description of the shared monitor config.
   */
  description?: string | null;
  classify_params: MinimalClassifyParams;
};
