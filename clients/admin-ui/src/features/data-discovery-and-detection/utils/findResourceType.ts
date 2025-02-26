import {
  StagedResourceAPIResponse,
  StagedResourceTypeValue,
} from "~/types/api";

export const findResourceType = (
  item: StagedResourceAPIResponse | undefined,
) => {
  if (!item) {
    return undefined;
  }
  if (item.resource_type) {
    return item.resource_type;
  }

  // Fallback to match the resource type based on the presence of
  // nested resources.
  if (item.schemas?.length) {
    return StagedResourceTypeValue.DATABASE;
  }
  if (item.tables?.length) {
    return StagedResourceTypeValue.SCHEMA;
  }
  if (item.fields?.length) {
    return StagedResourceTypeValue.TABLE;
  }
  return StagedResourceTypeValue.FIELD;
};
