import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";

const isNestedField = (resource: DiscoveryMonitorItem): boolean => {
  if (!resource.parent_table_urn) {
    // resource is not a field
    return false;
  }
  if (!resource.sub_field_urns?.length) {
    return false;
  }
  // make sure field is not a subfield
  return resource.urn.split(".").length === 5;
};

export default isNestedField;
