import { AddConnectionStep } from "datastore-connections/add-connection/types";

import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  SystemType,
} from "~/types/api";

export type ConnectionTypeParams = {
  search: string;
  system_type?: SystemType;
};

export type ConnectionTypeSecretSchemaProperty = {
  default?: string;
  title: string;
  type: string;
  description?: string;
  allOf?: {
    $ref: string;
  }[];
  items?: { $ref: string };
};

export type ConnectionTypeSecretSchemaReponse = {
  additionalProperties: boolean;
  description: string;
  properties: { [key: string]: ConnectionTypeSecretSchemaProperty };
  required: string[];
  title: string;
  type: string;
  definitions: {
    ExtendedIdentityTypes: ConnectionTypeSecretSchemaReponse;
    AdvancedSettingsWithExtendedIdentityTypes: ConnectionTypeSecretSchemaReponse;
  };
};

export type ConnectionTypeState = ConnectionTypeParams & {
  connection?: ConnectionConfigurationResponse;
  connectionOption?: ConnectionSystemTypeMap;
  connectionOptions: ConnectionSystemTypeMap[];
  step: AddConnectionStep;
};
