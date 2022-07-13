/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ContactDetails } from './ContactDetails';
import type { OrganizationMetadata } from './OrganizationMetadata';

/**
 * The Organization resource model.
 *
 * This resource is used as a way to organize all other resources.
 */
export type Organization = {
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
  /**
   * An inherited field from the FidesModel that is unused with an Organization.
   */
  organization_parent_key?: null;
  /**
   *
   * The contact details information model.
   *
   * Used to capture contact information for controllers, used
   * as part of exporting a data map / ROPA.
   *
   * This model is nested under an Organization and
   * potentially under a system/dataset.
   *
   */
  controller?: ContactDetails;
  /**
   *
   * The contact details information model.
   *
   * Used to capture contact information for controllers, used
   * as part of exporting a data map / ROPA.
   *
   * This model is nested under an Organization and
   * potentially under a system/dataset.
   *
   */
  data_protection_officer?: ContactDetails;
  /**
   *
   * The OrganizationMetadata resource model.
   *
   * Object used to hold application specific metadata for an organization
   *
   */
  fidesctl_meta?: OrganizationMetadata;
  /**
   *
   * The contact details information model.
   *
   * Used to capture contact information for controllers, used
   * as part of exporting a data map / ROPA.
   *
   * This model is nested under an Organization and
   * potentially under a system/dataset.
   *
   */
  representative?: ContactDetails;
  /**
   * Am optional URL to the organization security policy.
   */
  security_policy?: string;
};
