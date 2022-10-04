import { DataCategory, DatasetField } from "~/types/api";

export interface ColumnMetadata {
  name: string;
  attribute: keyof DatasetField;
}

export enum EditableType {
  DATASET = "dataset",
  COLLECTION = "collection",
  FIELD = "field",
}

export interface DataCategoryWithConfidence extends DataCategory {
  confidence: number;
}
