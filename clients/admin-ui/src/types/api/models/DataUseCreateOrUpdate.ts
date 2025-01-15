/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

export type DataUseCreateOrUpdate = {
  /**
   * The version of Fideslang in which this label was added.
   */
  version_added?: string | null;
  /**
   * The version of Fideslang in which this label was deprecated.
   */
  version_deprecated?: string | null;
  /**
   * The new name, if applicable, for this label after deprecation.
   */
  replaced_by?: string | null;
  /**
   * Denotes whether the resource is part of the default taxonomy or not.
   */
  is_default?: boolean;
  name?: string | null;
  description: string | null;
  active?: boolean | null;
  fides_key?: string | null;
  tags?: Array<string> | null;
  organization_fides_key?: string | null;
  parent_key?: string | null;
};
