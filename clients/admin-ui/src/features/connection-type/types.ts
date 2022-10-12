import { AddConnectionStep } from "datastore-connections/add-connection/types";
import { SystemType } from "datastore-connections/constants";
import { DatastoreConnection } from "datastore-connections/types";

import { ConnectionSystemTypeMap } from "~/types/api";

export type ConnectionTypeParams = {
  search: string;
  system_type?: SystemType;
};

export type ConnectionTypeSecretSchemaReponse = {
  additionalProperties: boolean;
  description: string;
  properties: {
    [key: string]: {
      default?: string;
      title: string;
      type: string;
    };
  };
  required: string[];
  title: string;
  type: string;
};

export type ConnectionTypeState = ConnectionTypeParams & {
  connection?: DatastoreConnection;
  connectionOption?: ConnectionSystemTypeMap;
  connectionOptions: ConnectionSystemTypeMap[];
  step: AddConnectionStep;
};
