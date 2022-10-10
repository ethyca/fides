import { AddConnectionStep } from "datastore-connections/add-connection/types";
import { SystemType } from "datastore-connections/constants";
import { DatastoreConnection } from "datastore-connections/types";

export type AllConnectionTypesResponse = {
  items: ConnectionOption[];
  total: number;
  page: number;
  size: number;
};

export type ConnectionOption = {
  identifier: string;
  human_readable: string;
  type: SystemType;
};

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
  connectionOption?: ConnectionOption;
  connectionOptions: ConnectionOption[];
  step: AddConnectionStep;
};
