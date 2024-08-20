/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * MySQL Secrets Schema for API Docs
 */
export type MySQLDocsSchema = {
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
  /**
   * Indicates whether an SSH tunnel is required for the connection. Enable this option if your MySQL server is behind a firewall and requires SSH tunneling for remote connections.
   */
  ssh_required?: boolean;
};
