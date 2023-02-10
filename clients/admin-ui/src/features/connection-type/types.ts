import { AddConnectionStep } from "datastore-connections/add-connection/types";
import { DatastoreConnection } from "datastore-connections/types";

import {
  AdvancedSettings,
  ConnectionSystemTypeMap,
  CookieIds,
  IdentityTypes,
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
    AdvancedSettings: {
      title: string;
      type: string;
      properties: { [key: string]: ConnectionTypeSecretSchemaProperty };
    };
    IdentityTypes: IdentityTypes;
    CookieIds: CookieIds;
  };
};

export type ConnectionTypeState = ConnectionTypeParams & {
  connection?: DatastoreConnection;
  connectionOption?: ConnectionSystemTypeMap;
  connectionOptions: ConnectionSystemTypeMap[];
  step: AddConnectionStep;
};
