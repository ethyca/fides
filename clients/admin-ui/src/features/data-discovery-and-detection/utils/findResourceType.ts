import { StagedResourceType } from "~/features/data-discovery-and-detection/types/StagedResourceType";
import { StagedResourceAPIResponse } from "~/types/api";

export const findResourceType = (
  item: StagedResourceAPIResponse | undefined
) => {
  if (!item) {
    return StagedResourceType.NONE;
  }
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
