import { CustomFieldsFormValues } from "~/features/common/custom-fields";
import { TreeNode } from "~/features/common/types";

export interface TaxonomyEntityNode extends TreeNode {
  description?: string;
  children: TaxonomyEntityNode[];
  is_default: boolean;
  active: boolean;
}

export interface TaxonomyEntity {
  fides_key: string;
  name?: string | null;
  description?: string | null;
  parent_key?: string | null;
  is_default?: boolean;
  active?: boolean;
  version_added?: string | null;
  version_deprecated?: string | null;
  replaced_by?: string | null;
}

export interface Labels {
  fides_key: string;
  name: string;
  description: string;
  parent_key?: string;
}

export type FormValues = Partial<TaxonomyEntity> &
  Pick<TaxonomyEntity, "fides_key"> &
  CustomFieldsFormValues;
