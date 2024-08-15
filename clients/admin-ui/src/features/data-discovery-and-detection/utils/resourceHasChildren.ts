import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";
import { StagedResourceType } from "~/features/data-discovery-and-detection/types/StagedResourceType";
import { findResourceType } from "~/features/data-discovery-and-detection/utils/findResourceType";
import isNestedField from "~/features/data-discovery-and-detection/utils/isNestedField";

const resourceHasChildren = (resource: DiscoveryMonitorItem): boolean => {
  const resourceType = findResourceType(resource);
  if (resourceType === StagedResourceType.FIELD) {
    return isNestedField(resource);
  }
  return true;
};

export default resourceHasChildren;
