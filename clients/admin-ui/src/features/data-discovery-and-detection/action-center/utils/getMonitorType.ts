import { ConnectionType } from "~/types/api";

// eslint-disable-next-line @typescript-eslint/naming-convention
export enum MONITOR_TYPES {
  WEBSITE = "website",
  DATASTORE = "datastore",
  INFRASTRUCTURE = "infrastructure",
}

export const getMonitorType = (connectionType: ConnectionType) => {
  if (
    connectionType === ConnectionType.WEBSITE ||
    connectionType === ConnectionType.TEST_WEBSITE
  ) {
    return MONITOR_TYPES.WEBSITE;
  }
  if (connectionType === ConnectionType.OKTA) {
    return MONITOR_TYPES.INFRASTRUCTURE;
  }
  return MONITOR_TYPES.DATASTORE;
};
