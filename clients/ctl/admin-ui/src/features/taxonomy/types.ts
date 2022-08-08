export interface TaxonomyEntityNode {
  value: string;
  label: string;
  description?: string;
  children: TaxonomyEntityNode[];
}

export interface TaxonomyEntity {
  fides_key: string;
  name?: string;
  description?: string;
  parent_key?: string | null;
}
