/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The component type - not formalized in the db
 */
export enum ComponentType {
  OVERLAY = "overlay", // deprecated, replaced by BANNER_AND_MODAL
  BANNER_AND_MODAL = "banner_and_modal",
  MODAL = "modal",
  PRIVACY_CENTER = "privacy_center",
  TCF_OVERLAY = "tcf_overlay",
}
