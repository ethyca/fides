import { TreeNode } from "../checkbox-tree/types";

export interface TaxonomyEntityNode extends TreeNode {
  description?: string | null;
  children: TaxonomyEntityNode[];
  is_default: boolean;
}

export interface TaxonomyEntity {
  fides_key: string;
  name?: string | null;
  description?: string | null;
  parent_key?: string | null;
  is_default?: boolean;
}
