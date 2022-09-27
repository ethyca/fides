import { DatasetField } from "~/types/api";

export interface ColumnMetadata {
  name: string;
  attribute: keyof DatasetField;
}

export enum EditableType {
  DATASET = "dataset",
  COLLECTION = "collection",
  FIELD = "field",
}
