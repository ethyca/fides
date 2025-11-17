/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DiffStatus } from "./DiffStatus";
import type { ErrorType } from "./ErrorType";

/**
 * Model for storing error information on a staged resource
 */
export type ResourceError = {
  /**
   * Error message
   */
  message: string;
  /**
   * When the error occurred
   */
  timestamp: string;
  /**
   * Type of error
   */
  error_type?: ErrorType;
  /**
   * The error `diff_status`, which indicates the phase in which the error occurred
   */
  diff_status: DiffStatus;
  /**
   * ID of the task that encountered the error
   */
  task_id?: string | null;
};
