/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Cookies } from "./Cookies";
import type { LegalBasisForProcessingEnum } from "./LegalBasisForProcessingEnum";
import type { SpecialCategoryLegalBasisEnum } from "./SpecialCategoryLegalBasisEnum";

/**
 * The PrivacyDeclaration resource model.
 *
 * States a function of a system, and describes how it relates
 * to the privacy data types.
 */
export type PrivacyDeclaration = {
  /**
   * The name of the privacy declaration on the system.
   */
  name?: string | null;
  /**
   * An array of data categories describing a system in a privacy declaration.
   */
  data_categories: Array<string>;
  /**
   * The Data Use describing a system in a privacy declaration.
   */
  data_use: string;
  /**
   * An array of data subjects describing a system in a privacy declaration.
   */
  data_subjects?: Array<string>;
  /**
   * Referenced Dataset fides keys used by the system.
   */
  dataset_references?: Array<string> | null;
  /**
   * The resources to which data is sent. Any `fides_key`s included in this list reference `DataFlow` entries in the `egress` array of any `System` resources to which this `PrivacyDeclaration` is applied.
   */
  egress?: Array<string> | null;
  /**
   * The resources from which data is received. Any `fides_key`s included in this list reference `DataFlow` entries in the `ingress` array of any `System` resources to which this `PrivacyDeclaration` is applied.
   */
  ingress?: Array<string> | null;
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
  legal_basis_for_processing?: LegalBasisForProcessingEnum | null;
  /**
   * Where the legitimate interest impact assessment is stored
   */
  impact_assessment_location?: string | null;
  /**
   * An optional string to describe the time period for which data is retained for this purpose.
   */
  retention_period?: string | null;
  /**
   * This system processes special category data
   */
  processes_special_category_data?: boolean;
  /**
   * The legal basis under which the special category data is processed.
   */
  special_category_legal_basis?: SpecialCategoryLegalBasisEnum | null;
  /**
   * This system shares data with third parties for this purpose.
   */
  data_shared_with_third_parties?: boolean;
  /**
   * The types of third parties the data is shared with.
   */
  third_parties?: string | null;
  /**
   * The categories of personal data that this system shares with third parties.
   */
  shared_categories?: Array<string>;
  /**
   * Cookies associated with this data use to deliver services and functionality
   */
  cookies?: Array<Cookies> | null;
};
