import { StagedResourceType } from "~/features/data-discovery-and-detection/types/StagedResourceType";
import { StagedResourceAPIResponse } from "~/types/api";

export const findResourceType = (
  item: StagedResourceAPIResponse | undefined,
) => {
  if (!item) {
    return StagedResourceType.NONE;
  }
  if (item.resource_type) {
    return item.resource_type as StagedResourceType;
  }

  // Fallback to match the resource type based on the presence of
  // nested resources.
  if (item.schemas?.length) {
    return StagedResourceType.DATABASE;
  }
  if (item.tables?.length) {
    return StagedResourceType.SCHEMA;
  }
  if (item.fields?.length) {
    return StagedResourceType.TABLE;
  }
  return StagedResourceType.FIELD;
};
