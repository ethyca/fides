/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * SQL dry run mode for controlling execution of SQL statements in privacy requests
 */
export enum SqlDryRunMode {
  NONE = "none",
  ACCESS = "access",
  ERASURE = "erasure",
}

export type ExecutionApplicationConfig = {
  subject_identity_verification_required?: boolean | null;
  disable_consent_identity_verification?: boolean | null;
  require_manual_request_approval?: boolean | null;
  sql_dry_run?: SqlDryRunMode | null;
};
