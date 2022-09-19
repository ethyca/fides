import { DatasetField } from "~/types/api";

export interface ColumnMetadata {
  name: string;
  attribute: keyof DatasetField;
}
