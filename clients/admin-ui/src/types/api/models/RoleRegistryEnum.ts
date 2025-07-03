/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Enum of available roles
 *
 * Owner - Full admin
 * Viewer - Can view everything
 * Approver - Limited viewer but can approve Privacy Requests
 * Viewer + Approver = Full View and can approve Privacy Requests
 * Contributor - Can't configure storage and messaging
 * Respondent - Internal user who can respond to manual steps
 * External Respondent - External user who can only respond to assigned manual steps
 */
export enum RoleRegistryEnum {
  OWNER = "owner",
  VIEWER_AND_APPROVER = "viewer_and_approver",
  VIEWER = "viewer",
  APPROVER = "approver",
  CONTRIBUTOR = "contributor",
  RESPONDENT = "respondent",
  EXTERNAL_RESPONDENT = "external_respondent",
}
