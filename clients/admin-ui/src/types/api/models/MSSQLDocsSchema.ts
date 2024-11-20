/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * MS SQL Secrets Schema for API Docs
 */
export type MSSQLDocsSchema = {
  /**
   * The hostname or IP address of the server where the database is running.
   */
  host: string;
  /**
   * The network port number on which the server is listening for incoming connections (default: 1433).
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
   * The name of the specific database within the database server that you want to connect to.
   */
  dbname?: string | null;
};
