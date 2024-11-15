import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";

const MAX_NON_NESTED_URN_LENGTH = 5;
const URN_SEPARATOR = ".";
/**
 * Helper method for deriving a resource's display name from its URN
 */
const getResourceName = ({
  name,
  urn,
  monitor_config_id,
  database_name,
  schema_name,
  table_name,
  top_level_field_name,
}: DiscoveryMonitorItem) => {
  const splitUrn = urn.split(URN_SEPARATOR);

  if (
    !table_name ||
    !top_level_field_name ||
    splitUrn.length < MAX_NON_NESTED_URN_LENGTH
  ) {
    // use name as-is if it's not a subfield
    return name;
  }
  // URN format is "monitor.project?.dataset.table.field.[any number of subfields]"
  // we want to show all subfield names separated by "."
  const partsToRemove = [
    monitor_config_id,
    database_name,
    schema_name,
    table_name,
    top_level_field_name,
  ];

  partsToRemove.forEach((part) => {
    const index = splitUrn.indexOf(part!);
    if (index > -1) {
      splitUrn.splice(index, 1);
    }
  });

  return splitUrn.join(URN_SEPARATOR);
};

export default getResourceName;
