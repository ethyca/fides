/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SystemScannerStatus } from "./SystemScannerStatus";

/**
 * Healthcheck schema
 */
export type HealthCheck = {
  core_fides_version: string;
  fidesplus_version: string;
  fidesplus_server: string;
  system_scanner: SystemScannerStatus;
};
