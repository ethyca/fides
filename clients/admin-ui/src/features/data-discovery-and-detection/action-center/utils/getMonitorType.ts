import { ConnectionType } from "~/types/api";
import { APIMonitorType } from "~/types/api/models/APIMonitorType";

export const getMonitorType = (connectionType: ConnectionType) => {
  if (
    connectionType === ConnectionType.WEBSITE ||
    connectionType === ConnectionType.TEST_WEBSITE
  ) {
    return APIMonitorType.WEBSITE;
  }
  if (
    connectionType === ConnectionType.OKTA ||
    connectionType === ConnectionType.ENTRA
  ) {
    return APIMonitorType.INFRASTRUCTURE;
  }
  if (connectionType === ConnectionType.AWS) {
    return APIMonitorType.CLOUD_INFRASTRUCTURE;
  }
  return APIMonitorType.DATASTORE;
};
