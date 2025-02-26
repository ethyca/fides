/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The ResourceFilter resource model.
 */
export type ResourceFilter = {
  /**
   * The type of filter to be used (i.e. ignore_resource_arn)
   */
  type: string;
  /**
   * A string representation of resources to be filtered. Can include wildcards.
   */
  value: string;
};
