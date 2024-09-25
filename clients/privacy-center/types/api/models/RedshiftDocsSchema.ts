/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Redshift Secrets Schema for API Docs
 */
export type RedshiftDocsSchema = {
  /**
   * The hostname or IP address of the server where the database is running.
   */
  host: string;
  /**
   * The network port number on which the server is listening for incoming connections (default: 5439).
   */
  port?: number;
  /**
   * The user account used to authenticate and access the database.
   */
  user: string;
  /**
   * The password used to authenticate and access the database.
   */
  password: string;
  /**
   * The name of the specific database within the database server that you want to connect to.
   */
  database: string;
  /**
   * The default schema to be used for the database connection (defaults to public).
   */
  db_schema?: string | null;
  /**
   * Indicates whether an SSH tunnel is required for the connection. Enable this option if your Redshift database is behind a firewall and requires SSH tunneling for remote connections.
   */
  ssh_required?: boolean;
};
