import { StagedResource } from "~/types/api";

const getResourceRowName = (row: StagedResource) =>
  `${row.monitor_config_id}-${row.name ?? row.urn}`;

export default getResourceRowName;
