/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Request model for performing actions on filtered fields with optional exclusions
 */
export type FilteredFieldActionRequest = {
  /**
   * List of resource URNs to exclude from the action
   */
  excluded_resource_urns?: Array<string>;
};
