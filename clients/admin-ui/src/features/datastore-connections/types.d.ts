import {
  ConnectionConfigurationResponse,
  ConnectionType,
  DatasetConfigCtlDataset,
  SystemType,
} from "~/types/api";

import {
  ConnectionTestStatus,
  DisabledStatus,
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

export type GetAllEnabledAccessManualWebhooksResponse =
  GetAccessManualWebhookResponse[];

export type GetAccessManualWebhookResponse = CreateAccessManualWebhookResponse;

export type PatchAccessManualWebhookRequest = CreateAccessManualWebhookRequest;

export type PatchAccessManualWebhookResponse =
  CreateAccessManualWebhookResponse;

export type PatchDatasetsConfigRequest = {
  connection_key: string;
  dataset_pairs: DatasetConfigCtlDataset[];
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
  fidesctl_meta: {
    resource_id: string;
  };
  collections: DatasetCollection[];
  fidesops_meta: {
    after: string[];
  };
};

export type DatasetCollection = {
  name: string;
  description: string;
  data_categories: string[];
  fields: DatasetCollectionField[];
};

export type DatasetCollectionField = {
  name: string;
  description: string;
  data_categories: string[];
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
  succeeded: ConnectionConfigurationResponse[];
  failed: [
    {
      message: string;
      data: object;
    },
  ];
};

export type DatastoreConnectionParams = {
  search: string;
  connection_type?: string[];
  test_status?: TestingStatus;
  system_type?: SystemType;
  disabled_status?: DisabledStatus;
  orphaned_from_system?: boolean;
  page: number;
  size: number;
};

export type DatastoreConnectionsResponse = {
  items: ConnectionConfigurationResponse[];
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

export type CreateSaasConnectionConfigRequest = {
  name: string;
  description: string;
  instance_key: string;
  saas_connector_type: string;
  secrets: {
    [key: string]: any;
  };
};

export type CreateSaasConnectionConfigResponse = {
  connection: ConnectionConfigurationResponse;
  dataset: {
    fides_key: string;
  };
};
