import { FidesBase, FidesKey } from "../common/fides-types";

export interface DataCategory extends FidesBase {
  parent_key: FidesKey | null;
}

export interface DataCategoryNode {
  value: string;
  label: string;
  description?: string;
  children: DataCategoryNode[];
}
