/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Cluster health options
 */
export enum ClusterHealth {
  CONNECTED = "connected",
  DEGRADED = "degraded",
  DISCONNECTED = "disconnected",
  HEALTHY = "healthy",
  UNHEALTHY = "unhealthy",
  UNKNOWN = "unknown",
  UNREACHABLE = "unreachable",
  UPDATE_FAILED = "update_failed",
  UPDATING = "updating",
}
