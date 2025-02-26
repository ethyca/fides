/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * MariaDB Secrets Schema for API Docs
 */
export type MariaDBDocsSchema = {
  /**
   * The hostname or IP address of the server where the database is running.
   */
  host: string;
  /**
   * The network port number on which the server is listening for incoming connections (default: 3306).
   */
  port?: number;
  /**
   * The user account used to authenticate and access the database.
   */
  username?: string | null;
  /**
   * The password used to authenticate and access the database.
   */
  password?: string | null;
  /**
   * The name of the specific database within the database server that you want to connect to.
   */
  dbname: string;
};
