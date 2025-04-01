/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Reject all mechanism options - not formalized in the db.
 * Used to configure the behavior of the reject all button in TCF experiences
 */
export enum RejectAllMechanism {
  REJECT_ALL = "reject_all",
  REJECT_CONSENT_ONLY = "reject_consent_only",
}
