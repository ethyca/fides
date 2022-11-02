/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response after creating, editing, or retrieving a FidesUserPermissions record
 */
export type UserPermissionsResponse = {
  scopes: Array<string>;
  id: string;
  user_id: string;
};
