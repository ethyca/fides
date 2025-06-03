import { AddConnectionStep } from "datastore-connections/add-connection/types";

import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  SystemType,
} from "~/types/api";

export type ConnectionTypeParams = {
  search: string;
  system_type?: SystemType;
  page?: number;
  size?: number;
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
  sensitive?: boolean;
  options?: string[];
};

export type ConnectionTypeSecretSchemaResponse = {
  additionalProperties: boolean;
  description: string;
  properties: { [key: string]: ConnectionTypeSecretSchemaProperty };
  required: string[];
  title: string;
  type: string;
  definitions: {
    [key: string]: {
      enum?: string[];
      title: string;
      type: string;
    };
    ExtendedIdentityTypes: ConnectionTypeSecretSchemaResponse;
    AdvancedSettingsWithExtendedIdentityTypes: ConnectionTypeSecretSchemaResponse;
  };
};

export type ConnectionTypeState = ConnectionTypeParams & {
  connection?: ConnectionConfigurationResponse;
  connectionOption?: ConnectionSystemTypeMap;
  connectionOptions: ConnectionSystemTypeMap[];
  step: AddConnectionStep;
};
