export interface DataCategoryNode {
  value: string;
  label: string;
  description?: string;
  children: DataCategoryNode[];
}
