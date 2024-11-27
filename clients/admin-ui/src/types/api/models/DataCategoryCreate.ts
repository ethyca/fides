/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

export type DataCategoryCreate = {
  name?: string | null;
  description: string;
  active?: boolean;
  fides_key?: string | null;
  is_default?: boolean;
  tags?: Array<string> | null;
  organization_fides_key?: string | null;
  parent_key?: string | null;
};
