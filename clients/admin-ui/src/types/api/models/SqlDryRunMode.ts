/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * SQL dry run mode for controlling execution of SQL statements in privacy requests
 */
export enum SqlDryRunMode {
  NONE = 'none',
  ACCESS = 'access',
  ERASURE = 'erasure',
}
