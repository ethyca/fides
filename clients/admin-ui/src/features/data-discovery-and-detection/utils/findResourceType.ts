import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";

import { StagedResourceType } from "../types/StagedResourceType";

export const findResourceType = (item: DiscoveryMonitorItem | undefined) => {
  if (!item) {
    return StagedResourceType.NONE;
  }
  if (item.schemas) {
    return StagedResourceType.DATABASE;
  }
  if (item.tables) {
    return StagedResourceType.SCHEMA;
  }
  if (item.fields) {
    return StagedResourceType.TABLE;
  }
  return StagedResourceType.FIELD;
};
