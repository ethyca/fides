/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Mongo DB Secrets Schema for API docs
 */
export type MongoDBDocsSchema = {
  /**
   * The hostname or IP address of the server where the database is running.
   */
  host: string;
  /**
   * The network port number on which the server is listening for incoming connections (default: 27017). Port will be ignored if using SRV.
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
   * Used to specify the default authentication database.
   */
  defaultauthdb: string;
  /**
   * Enable SRV record lookup for service discovery (mongodb+srv://). Required for MongoDB Atlas. Enables SSL by default.
   */
  use_srv?: (boolean | null);
  /**
   * Enable SSL/TLS encryption. With SRV: defaults to enabled (can override). Without SRV: defaults to disabled.
   */
  ssl_enabled?: (boolean | null);
};

