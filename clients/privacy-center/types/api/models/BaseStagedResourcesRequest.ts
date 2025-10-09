/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Request model for bulk operations on staged resources
 */
export type BaseStagedResourcesRequest = {
  /**
   * List of staged resource URNs to act on
   */
  staged_resource_urns: Array<string>;
};
