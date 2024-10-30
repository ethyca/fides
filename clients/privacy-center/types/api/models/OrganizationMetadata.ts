/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ResourceFilter } from "./ResourceFilter";

/**
 * The OrganizationMetadata resource model.
 *
 * Object used to hold application specific metadata for an organization
 */
export type OrganizationMetadata = {
  /**
   * A list of filters that can be used when generating or scanning systems.
   */
  resource_filters?: Array<ResourceFilter> | null;
};
