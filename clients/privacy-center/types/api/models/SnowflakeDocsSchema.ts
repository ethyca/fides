/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Snowflake Secrets Schema for API Docs
 */
export type SnowflakeDocsSchema = {
  /**
   * The unique identifier for your Snowflake account.
   */
  account_identifier: string;
  /**
   * The user account used to authenticate and access the database.
   */
  user_login_name: string;
  /**
   * The password used to authenticate and access the database. You can use a password or a private key, but not both.
   */
  password?: string | null;
  /**
   * The private key used to authenticate and access the database. If a `private_key_passphrase` is also provided, it is assumed to be encrypted; otherwise, it is assumed to be unencrypted.
   */
  private_key?: string | null;
  /**
   * The passphrase used for the encrypted private key.
   */
  private_key_passphrase?: string | null;
  /**
   * The name of the Snowflake warehouse where your queries will be executed.
   */
  warehouse_name: string;
  /**
   * The name of the Snowflake database you want to connect to.
   */
  database_name: string;
  /**
   * The name of the Snowflake schema within the selected database.
   */
  schema_name: string;
  /**
   * The Snowflake role to assume for the session, if different than Username.
   */
  role_name?: string | null;
};
