/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The component type - not formalized in the db
 *
 * Overlay type has been deprecated but can't be removed for backwards compatibility
 * without significant data migrations.
 */
export enum ComponentType {
  OVERLAY = "overlay",
  BANNER_AND_MODAL = "banner_and_modal",
  MODAL = "modal",
  PRIVACY_CENTER = "privacy_center",
  TCF_OVERLAY = "tcf_overlay",
  HEADLESS = "headless",
}
