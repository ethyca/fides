/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response model for promoted resources, containing the staged resource URN, name, system_id, user_assigned_system_id, and user_assigned_system_key
 */
export type PromotedResourceResponse = {
  urn: string;
  name: string;
  promoted_system_id?: string | null;
  promoted_system_key?: string | null;
};
