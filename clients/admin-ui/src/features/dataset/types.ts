import { DataCategory } from "~/types/api";

export interface DataCategoryWithConfidence extends DataCategory {
  confidence?: number | null;
}
