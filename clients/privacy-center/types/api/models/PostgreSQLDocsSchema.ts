/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Postgres Secrets Schema for API Docs
 */
export type PostgreSQLDocsSchema = {
  /**
   * The hostname or IP address of the server where the database is running.
   */
  host: string;
  /**
   * The network port number on which the server is listening for incoming connections (default: 5432).
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
  /**
   * The default schema to be used for the database connection (defaults to public).
   */
  db_schema?: string | null;
  /**
   * Indicates whether an SSH tunnel is required for the connection. Enable this option if your PostgreSQL server is behind a firewall and requires SSH tunneling for remote connections.
   */
  ssh_required?: boolean;
};
