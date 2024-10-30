/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Worker Healthcheck Schema
 */
export type WorkerHealthCheck = {
  workers_enabled: boolean;
  workers: Array<string>;
  queue_counts: Record<string, number>;
};
