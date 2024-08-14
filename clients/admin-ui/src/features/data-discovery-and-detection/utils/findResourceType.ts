import { StagedResourceType } from "~/features/data-discovery-and-detection/types/StagedResourceType";
import { StagedResourceAPIResponse } from "~/types/api";

export const findResourceType = (
  item: StagedResourceAPIResponse | undefined,
) => {
  if (!item) {
    return StagedResourceType.NONE;
  }
  if (item.schemas) {
    return StagedResourceType.DATABASE;
  }
  if (item.tables) {
    return StagedResourceType.SCHEMA;
  }
  if (item.fields) {
    return StagedResourceType.TABLE;
  }
  return StagedResourceType.FIELD;
};
