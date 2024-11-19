import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";

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
  top_level_field_urn,
}: DiscoveryMonitorItem) => {
  // use name as-is if resource is not a subfield
  if (!top_level_field_name) {
    return name;
  }

  const splitUrn = urn.split(URN_SEPARATOR);
  // for subfields, we want to show all subfield names separated by "."
  // format is "monitor.project?.dataset.table.field.[any number of subfields]"

  // this case *should* catch all subfields
  if (top_level_field_urn) {
    return urn.replace(`${top_level_field_urn}${URN_SEPARATOR}`, "");
  }

  // as a fallback, parse URN manually and remove higher-level segments
  const segmentsToRemove = [
    monitor_config_id,
    database_name,
    schema_name,
    table_name,
    top_level_field_name,
  ];

  segmentsToRemove.forEach((part) => {
    if (part) {
      const index = splitUrn.indexOf(part);
      if (index > -1) {
        splitUrn.splice(index, 1);
      }
    }
  });

  return splitUrn.join(URN_SEPARATOR);
};

export default getResourceName;
