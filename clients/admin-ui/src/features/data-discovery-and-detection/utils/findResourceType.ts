import { Database, Field, Schema, StagedResource, Table } from "~/types/api";

import { StagedResourceType } from "../types/StagedResourceType";

export type MonitorResultsItem = StagedResource &
  Partial<Database & Schema & Table & Field>;

export const findResourceType = (item: MonitorResultsItem | undefined) => {
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
