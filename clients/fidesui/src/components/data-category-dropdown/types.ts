import { TreeNode } from "../checkbox-tree/types";

export interface TaxonomyEntityNode extends TreeNode {
  description?: string;
  children: TaxonomyEntityNode[];
  is_default: boolean;
}

export interface TaxonomyEntity {
  fides_key: string;
  name?: string;
  description?: string;
  parent_key?: string;
  is_default?: boolean;
}
