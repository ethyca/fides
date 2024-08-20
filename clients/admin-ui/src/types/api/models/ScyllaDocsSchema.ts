/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Scylla Secrets Schema for API docs
 */
export type ScyllaDocsSchema = {
  /**
   * The hostname or IP address of the server where the database is running.
   */
  host: string;
  /**
   * The network port number on which the server is listening for incoming connections (default: 9042).
   */
  port?: number;
  /**
   * The user account used to authenticate and access the database.
   */
  username: string;
  /**
   * The password used to authenticate and access the database.
   */
  password: string;
  /**
   * The keyspace used. If not provided, DSRs for this integration will error. If the integration is used for D & D, then setting a keyspace is not required.
   */
  keyspace?: string | null;
};
