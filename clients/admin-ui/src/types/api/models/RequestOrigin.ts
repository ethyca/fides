/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * We currently extract the RequestOrigin from the Privacy Experience
 * Config ComponentType when saving, so RequestOrigin needs to be a
 * superset of ComponentType.
 *
 * Not at the db level due to being subject to change.
 * Only add here, do not remove
 */
export enum RequestOrigin {
  PRIVACY_CENTER = "privacy_center",
  OVERLAY = "overlay",
  MODAL = "modal",
  BANNER_AND_MODAL = "banner_and_modal",
  API = "api",
  TCF_OVERLAY = "tcf_overlay",
  HEADLESS = "headless",
}
