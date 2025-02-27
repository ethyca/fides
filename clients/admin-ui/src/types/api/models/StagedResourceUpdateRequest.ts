/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Defines the subset of StagedResource fields permissable on update request payloads
 */
export type StagedResourceUpdateRequest = {
  urn: string;
  /**
   * The data uses associated with the resource
   */
  data_uses?: Array<string> | null;
  user_assigned_data_categories?: Array<string>;
  system_key?: string | null;
};
