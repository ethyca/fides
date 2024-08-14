import { GenericStagedResource } from "~/types/api";

import { StagedResourceType } from "../types/StagedResourceType";

export const findResourceType = (item: GenericStagedResource | undefined) => {
  if (!item) {
    return StagedResourceType.NONE;
  }
  if (item.tables) {
    return StagedResourceType.SCHEMA;
  }
  if (item.fields) {
    return StagedResourceType.TABLE;
  }
  return StagedResourceType.FIELD;
};
