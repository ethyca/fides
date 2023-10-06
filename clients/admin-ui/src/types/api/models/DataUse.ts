/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { LegalBasisEnum } from "./LegalBasisEnum";
import type { SpecialCategoriesEnum } from "./SpecialCategoriesEnum";

/**
 * The DataUse resource model.
 */
export type DataUse = {
  /**
   * The version of Fideslang in which this label was added.
   */
  version_added?: string;
  /**
   * The version of Fideslang in which this label was deprecated.
   */
  version_deprecated?: string;
  /**
   * The new name, if applicable, for this label after deprecation.
   */
  replaced_by?: string;
  /**
   * Denotes whether the resource is part of the default taxonomy or not.
   */
  is_default?: boolean;
  /**
   * A unique key used to identify this resource.
   */
  fides_key: string;
  /**
   * Defines the Organization that this resource belongs to.
   */
  organization_fides_key?: string;
  tags?: Array<string>;
  /**
   * Human-Readable name for this resource.
   */
  name?: string;
  /**
   * A detailed description of what this resource is.
   */
  description?: string;
  parent_key?: string;
  /**
   * Deprecated. The legal basis category of which the data use falls under. This field is used as part of the creation of an exportable data map.
   */
  legal_basis?: LegalBasisEnum;
  /**
   * Deprecated. The special category for processing of which the data use falls under. This field is used as part of the creation of an exportable data map.
   */
  special_category?: SpecialCategoriesEnum;
  /**
   * Deprecated. An array of recipients when sharing personal data outside of your organization.
   */
  recipients?: Array<string>;
  /**
   * Deprecated. A boolean representation of if the legal basis used is `Legitimate Interest`. Validated at run time and looks for a `legitimate_interest_impact_assessment` to exist if true.
   */
  legitimate_interest?: boolean;
  /**
   * Deprecated. A url pointing to the legitimate interest impact assessment. Required if the legal bases used is legitimate interest.
   */
  legitimate_interest_impact_assessment?: string;
  /**
   * Indicates whether the resource is currently 'active'.
   */
  active?: boolean;
};
