import {
  AccessLevel,
  ConnectionTestStatus,
  ConnectionType,
  DisabledStatus,
  SaasType,
  SystemType,
  TestingStatus,
} from "./constants";

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
  saas_config?: SaasConfig;
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

export type DatastoreConnectionResponse = {
  items: DatastoreConnection[];
  total: number;
  page: number;
  size: number;
};

export type DatastoreConnectionStatus = {
  msg: string;
  test_status?: ConnectionTestStatus;
  failure_reason?: string;
};

export type DatastoreConnectionUpdate = {
  name: string;
  key: string;
  disabled: boolean;
  connection_type: ConnectionType;
  access: AccessLevel;
};

export type SaasConfig = {
  type: SaasType;
};
