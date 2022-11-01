import { DataCategory } from "~/types/api";

export enum EditableType {
  DATASET = "dataset",
  COLLECTION = "collection",
  FIELD = "field",
}

export interface DataCategoryWithConfidence extends DataCategory {
  confidence?: number;
}
