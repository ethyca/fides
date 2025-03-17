/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Defines the subset of StagedResource fields permissable on update request payloads
 */
export type StagedResourceUpdateRequest = {
  urn: string;
  user_assigned_data_categories?: Array<string> | null;
  /**
   * User assigned data uses overriding auto assigned data uses
   */
  user_assigned_data_uses?: Array<string> | null;
  user_assigned_system_key?: string | null;
};
