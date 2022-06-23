export enum ConnectionType {
  POSTGRES = "postgres",
  MONGODB = "mongodb",
  MYSQL = "mysql",
  HTTPS = "https",
  SAAS = "saas",
  REDSHIFT = "redshift",
  SNOWFLAKE = "snowflake",
  MSSQL = "mssql",
  MARIADB = "mariadb",
  BIGQUERY = "bigquery",
  MANUAL = "manual",
}

export enum SystemType {
  SAAS = "saas",
  DATABASE = "database",
  MANUAL = "manual",
}

export enum TestingStatus {
  PASSED = "passed",
  FAILED = "failed",
  UNTESTED = "untested",
}

export enum AccessLevel {
  READ = "read",
  WRITE = "write",
}

export enum DisabledStatus {
  ACTIVE = "active",
  DISABLED = "disabled",
}

export type DatastoreConnection = {
  name: string;
  key: string;
  description?: string;
  disabled: boolean;
  connection_type: ConnectionType;
  access: AccessLevel;
  created_at: string;
  updated_at?: string;
  last_test_timestamp: string;
  last_test_succeeded: boolean;
};

export type DatastoreConnectionResponse = {
  items: DatastoreConnection[];
  total: number;
  page: number;
  size: number;
};

export type DatastoreConnectionParams = {
  search: string;
  connection_type?: ConnectionType[];
  test_status?: TestingStatus;
  system_type?: SystemType;
  disabled_status?: DisabledStatus;
  page: number;
  size: number;
};

export enum ConnectionTestStatus {
  SUCCEEDED = "succeeded",
  FAILED = "failed",
  SKIPPED = "skipped",
}

export type DatastoreConnectionStatus = {
  msg: string;
  test_status?: ConnectionTestStatus;
  failure_reason?: string;
};

export interface DatastoreConnectionUpdate {
  name: string;
  key: string;
  disabled: boolean;
  connection_type: ConnectionType;
  access: AccessLevel;
}
