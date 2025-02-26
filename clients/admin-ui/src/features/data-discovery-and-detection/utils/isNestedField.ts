import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";

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
    // resource has no children
    return false;
  }
  // only true if resource is not a child of another field
  return !resource.top_level_field_name;
};

export default isNestedField;
