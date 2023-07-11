/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Cookies } from "./Cookies";

/**
 * Extension of base pydantic model to include DB `id` field in the response
 */
export type PrivacyDeclarationResponse = {
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
   * The fides key of the data qualifier describing a system in a privacy declaration.
   */
  data_qualifier?: string;
  /**
   * An array of data subjects describing a system in a privacy declaration.
   */
  data_subjects: Array<string>;
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
  cookies?: Array<Cookies>;
  /**
   * The database-assigned ID of the privacy declaration on the system. This is meant to be a read-only field, returned only in API responses
   */
  id: string;
};
