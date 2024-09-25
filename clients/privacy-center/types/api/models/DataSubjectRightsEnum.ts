/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The model for data subject rights over
 * personal data.
 *
 * Based upon chapter 3 of the GDPR
 */
export enum DataSubjectRightsEnum {
  INFORMED = "Informed",
  ACCESS = "Access",
  RECTIFICATION = "Rectification",
  ERASURE = "Erasure",
  PORTABILITY = "Portability",
  RESTRICT_PROCESSING = "Restrict Processing",
  WITHDRAW_CONSENT = "Withdraw Consent",
  OBJECT = "Object",
  OBJECT_TO_AUTOMATED_PROCESSING = "Object to Automated Processing",
}
