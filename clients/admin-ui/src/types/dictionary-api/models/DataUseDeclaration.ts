/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Cookie } from "./Cookie";
import type { LegalBasisForProcessingEnum } from "./LegalBasisForProcessingEnum";
import type { SpecialCategoryLegalBasisEnum } from "./SpecialCategoryLegalBasisEnum";

/**
 * A Compass data use declaration record, extending a fideslang `PrivacyDeclaration`
 */
export type DataUseDeclaration = {
  /**
   * The name of the privacy declaration on the system.
   */
  name?: string;
  /**
   * An array of data categories describing a system in a privacy declaration.
   */
  data_categories: Array<string>;
  /**
   * The Data Use describing a system in a privacy declaration.
   */
  data_use: string;
  /**
   * Deprecated. The fides key of the data qualifier describing a system in a privacy declaration.
   */
  data_qualifier?: string;
  /**
   * An array of data subjects describing a system in a privacy declaration.
   */
  data_subjects?: Array<string>;
  /**
   * Referenced Dataset fides keys used by the system.
   */
  dataset_references?: Array<string>;
  /**
   * The resources to which data is sent. Any `fides_key`s included in this list reference `DataFlow` entries in the `egress` array of any `System` resources to which this `PrivacyDeclaration` is applied.
   */
  egress?: Array<string>;
  /**
   * The resources from which data is received. Any `fides_key`s included in this list reference `DataFlow` entries in the `ingress` array of any `System` resources to which this `PrivacyDeclaration` is applied.
   */
  ingress?: Array<string>;
  /**
   * The features of processing personal data.
   */
  features?: Array<string>;
  /**
   * Whether the legal basis for processing is 'flexible' (i.e. can be overridden in a privacy notice) for this declaration.
   */
  flexible_legal_basis_for_processing?: boolean;
  /**
   * The legal basis under which personal data is processed for this purpose.
   */
  legal_basis_for_processing?: LegalBasisForProcessingEnum;
  /**
   * Where the legitimate interest impact assessment is stored
   */
  impact_assessment_location?: string;
  /**
   * An optional string to describe the time period for which data is retained for this purpose.
   */
  retention_period?: string;
  /**
   * This system processes special category data
   */
  processes_special_category_data?: boolean;
  /**
   * The legal basis under which the special category data is processed.
   */
  special_category_legal_basis?: SpecialCategoryLegalBasisEnum;
  /**
   * This system shares data with third parties for this purpose.
   */
  data_shared_with_third_parties?: boolean;
  /**
   * The types of third parties the data is shared with.
   */
  third_parties?: string;
  /**
   * The categories of personal data that this system shares with third parties.
   */
  shared_categories?: Array<string>;
  /**
   * The Cookies associated with the record
   */
  cookies?: Array<Cookie>;
  /**
   * The ID of the vendor that the record belongs to
   */
  vendor_id: string;
  /**
   * The name of the vendor that the record belongs to
   */
  vendor_name: string;
  /**
   * The GVL purpose associated with this data use declaration
   */
  purpose?: number;
  /**
   * The GVL special purpose associated with this data use declaration
   */
  special_purpose?: number;
  /**
   * The version of GVL from which the record is derived
   */
  gvl_version?: string;
};
