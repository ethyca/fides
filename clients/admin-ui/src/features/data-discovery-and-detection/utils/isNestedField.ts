import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";

export const TOP_LEVEL_FIELD_URN_LENGTH = 5;

/**
 * Helper method to determine whether a resource is a "top-level" field.
 * `true` if the resource is at top-level nested field; `false`if the
 * resource is not a field, has no subfields, or is a subfield of another field
 */
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
