/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Schema representing a single log entry
 */
export type LogEntry = {
  timestamp: string;
  level: string;
  module_info: string;
  message: string;
};
