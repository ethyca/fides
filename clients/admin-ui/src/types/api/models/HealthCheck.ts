/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SystemScannerStatus } from "./SystemScannerStatus";

/**
 * Healthcheck schema
 */
export type HealthCheck = {
  core_fidesctl_version: string;
  fidesctl_plus_server: string;
  fidescls_version: string;
  system_scanner: SystemScannerStatus;
};
