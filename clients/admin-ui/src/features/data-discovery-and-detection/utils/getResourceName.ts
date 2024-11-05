import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";

const TOP_LEVEL_FIELD_URN_PARTS = 5;

const getResourceName = (resource: DiscoveryMonitorItem) => {
  const URN_SEPARATOR = ".";
  const splitUrn = resource.urn.split(URN_SEPARATOR);
  if (
    !resource.parent_table_urn ||
    splitUrn.length === TOP_LEVEL_FIELD_URN_PARTS
  ) {
    // use name as-is if it's not a subfield
    return resource.name;
  }
  // TODO HJ-162: better handle case where field name contains "."

  // URN format is "monitor.project.dataset.field.[any number of subfields]"
  // for a subfield, we want to show all subfield names separated by "."
  return splitUrn.slice(TOP_LEVEL_FIELD_URN_PARTS).join(URN_SEPARATOR);
};

export default getResourceName;
