/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Defines the subset of StagedResource fields permissable on update request payloads
 */
export type StagedResourceUpdateRequest = {
  urn: string;
  user_assigned_data_categories?: Array<string>;
};
