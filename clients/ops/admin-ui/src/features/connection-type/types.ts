import { SaasType, SystemType } from "datastore-connections/constants";

export type ConnectionOption = {
  identifier: ConnectionType | SaasType;
  type: SystemType;
};

export type ConnectionTypeParams = {
  search: string;
  system_type?: SystemType;
};
