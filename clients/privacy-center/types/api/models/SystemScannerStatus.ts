/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ClusterHealth } from "./ClusterHealth";

/**
 * System scanner status schema
 */
export type SystemScannerStatus = {
  enabled?: boolean;
  cluster_health?: ClusterHealth | null;
  cluster_error?: string | null;
};
