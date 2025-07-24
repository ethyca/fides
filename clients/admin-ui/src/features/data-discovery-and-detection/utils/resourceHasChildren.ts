import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";
import { findResourceType } from "~/features/data-discovery-and-detection/utils/findResourceType";
import isNestedField from "~/features/data-discovery-and-detection/utils/isNestedField";
import { StagedResourceTypeValue } from "~/types/api";

const resourceHasChildren = (resource: DiscoveryMonitorItem): boolean => {
  const resourceType = findResourceType(resource);
  if (resourceType === StagedResourceTypeValue.FIELD) {
    return isNestedField(resource);
  }
  return true;
};

export default resourceHasChildren;
