import { RTKErrorResult } from "~/types/errors";

import { TreeNode } from "../common/types";

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

export interface Labels {
  fides_key: string;
  name: string;
  description: string;
  parent_key: string;
}

export type RTKResult<T> = Promise<
  | {
      data: T;
    }
  | { error: RTKErrorResult["error"] }
>;
