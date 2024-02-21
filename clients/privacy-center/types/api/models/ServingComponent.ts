/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * This differs from component type because we want to record exactly
 * where consent was served.
 *
 * Not at the db level due to being subject to change.
 * Only add here, do not remove
 */
export enum ServingComponent {
  OVERLAY = 'overlay',
  BANNER = 'banner',
  MODAL = 'modal',
  PRIVACY_CENTER = 'privacy_center',
  TCF_OVERLAY = 'tcf_overlay',
  TCF_BANNER = 'tcf_banner',
}
