import { RTKErrorResult } from "~/types/errors";

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
  parent_key?: string;
}

export interface Labels {
  fides_key: string;
  name: string;
  description: string;
  parent_key: string;
}

export type TaxonomyRTKResult = Promise<
  | {
      data: TaxonomyEntity;
    }
  | { error: RTKErrorResult["error"] }
>;
