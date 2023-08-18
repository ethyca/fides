/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Healthcheck schema
 */
export type CoreHealthCheck = {
  webserver: string;
  version: string;
  database: CoreHealthCheck.database;
  cache: CoreHealthCheck.cache;
  workers_enabled: boolean;
  workers: Array<string>;
};

export namespace CoreHealthCheck {
  export enum database {
    HEALTHY = "healthy",
    UNHEALTHY = "unhealthy",
  }

  export enum cache {
    HEALTHY = "healthy",
    UNHEALTHY = "unhealthy",
    NO_CACHE_CONFIGURED = "no cache configured",
  }
}
