/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Consent status of the asset
 */
export enum ConsentStatus {
  WITH_CONSENT = "with_consent",
  WITHOUT_CONSENT = "without_consent",
  EXEMPT = "exempt",
  UNKNOWN = "unknown",
  PRE_CONSENT = "pre_consent",
  CMP_ERROR = "cmp_error",
  NOT_APPLICABLE = "not_applicable",
}
