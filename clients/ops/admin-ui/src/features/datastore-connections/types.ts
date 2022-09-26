import {
  AccessLevel,
  ConnectionTestStatus,
  ConnectionType,
  DisabledStatus,
  SaasType,
  SystemType,
  TestingStatus,
} from "./constants";

export type AccessManualHookField = {
  pii_field: string;
  dsr_package_label: string;
};

export type CreateAccessManualWebhookRequest = {
  connection_key: string;
  body: {
    fields: AccessManualHookField[];
  };
};

export type CreateAccessManualWebhookResponse = {
  fields: AccessManualHookField[];
  connection_config: {
    name: string;
    key: string;
    description: string;
    connection_type: string;
    access: string;
    created_at: string;
    updated_at: string;
    disabled: boolean;
    last_test_timestamp: string;
    last_test_succeeded: string;
    saas_config: {
      fides_key: string;
      name: string;
      type: string;
    };
  };
  id: string;
};

export type GetAccessManualWebhookResponse = CreateAccessManualWebhookResponse;

export type PatchAccessManualWebhookRequest = CreateAccessManualWebhookRequest;

export type PatchAccessManualWebhookResponse =
  CreateAccessManualWebhookResponse;

export type PatchDatasetsRequest = {
  connection_key: string;
  datasets: Dataset[];
};

export type DatasetsReponse = {
  items: Dataset[];
  total: number;
  page: number;
  size: number;
};

export type Dataset = {
  fides_key: string;
  organization_fides_key: string;
  tags: string[];
  name: string;
  description: string;
  meta: {
    [key: string]: string;
  };
  data_categories: string[];
  data_qualifier: string;
  fidesctl_meta: {
    resource_id: string;
  };
  joint_controller: {
    name: string;
    address: string;
    email: string;
    phone: string;
  };
  retention: string;
  third_country_transfers: string[];
  collections: DatasetCollection[];
  fidesops_meta: {
    after: string[];
  };
};

export type DatasetCollection = {
  name: string;
  description: string;
  data_categories: string[];
  data_qualifier: string;
  retention: string;
  fields: DatasetCollectionField[];
};

export type DatasetCollectionField = {
  name: string;
  description: string;
  data_categories: string[];
  data_qualifier: string;
  retention: string;
  fidesops_meta: {
    references: FidesOpsMetaReference[];
    identity: string;
    primary_key: boolean;
    data_type: string;
    length: number;
    return_all_elements: boolean;
    read_only: boolean;
  };
  fields: DatasetCollection[];
};

export type FidesOpsMetaReference = {
  dataset: string;
  field: string;
  direction: string;
};

export type DatastoreConnectionRequest = {
  name: string;
  key?: string;
  connection_type: ConnectionType;
  access: string;
  disabled: boolean;
  description: string;
};

export type DatastoreConnectionResponse = {
  succeeded: DatastoreConnection[];
  failed: [
    {
      message: string;
      data: Object;
    }
  ];
};

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

export const isDatastoreConnection = (obj: any): obj is DatastoreConnection =>
  (obj as DatastoreConnection).connection_type !== undefined;

export type DatastoreConnectionParams = {
  search: string;
  connection_type?: ConnectionType[];
  test_status?: TestingStatus;
  system_type?: SystemType;
  disabled_status?: DisabledStatus;
  page: number;
  size: number;
};

export type DatastoreConnectionsResponse = {
  items: DatastoreConnection[];
  total: number;
  page: number;
  size: number;
};

export type DatastoreConnectionSecretsRequest = {
  connection_key: string;
  secrets: {
    [key: string]: any;
  };
};

export type DatastoreConnectionSecretsResponse = {
  msg: string;
  test_status: string;
  failure_reason: string;
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
  fides_key: string;
  name: string;
  type: SaasType;
};

export type CreateSassConnectionConfigRequest = {
  name: string;
  description: string;
  instance_key: string;
  saas_connector_type: SaasType;
  secrets: {
    [key: string]: any;
  };
};

export type CreateSassConnectionConfigResponse = {
  connection: DatastoreConnection;
  dataset: {
    fides_key: string;
  };
};
