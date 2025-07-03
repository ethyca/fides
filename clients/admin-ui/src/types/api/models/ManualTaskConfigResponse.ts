/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ManualTaskConfigurationType } from "./ManualTaskConfigurationType";
import type { ManualTaskFieldBase } from "./ManualTaskFieldBase";

/**
 * Schema for manual task configuration response.
 */
export type ManualTaskConfigResponse = {
  /**
   * Configuration ID
   */
  id: string;
  /**
   * Manual task ID
   */
  manual_task_id: string;
  /**
   * Type of configuration
   */
  config_type: ManualTaskConfigurationType;
  /**
   * Version of the configuration
   */
  version: number;
  /**
   * Whether this is the current version
   */
  is_current: boolean;
  /**
   * List of field definitions
   */
  fields: Array<ManualTaskFieldBase>;
  /**
   * Creation timestamp
   */
  created_at: string;
  /**
   * Last update timestamp
   */
  updated_at: string;
};
